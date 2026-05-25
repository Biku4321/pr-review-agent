import time
import json
import re
import os
from typing import Callable, Optional
import google.generativeai as genai
from models.schemas import AgentResult, ReviewIssue, Severity, IssueCategory

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

QUALITY_SYSTEM_PROMPT = """You are an expert code quality reviewer. Your ONLY job is to find code quality and maintainability issues.

Focus on:
- DRY violations (duplicated logic that should be extracted)
- Functions doing too many things (single responsibility principle)
- Overly complex functions (cyclomatic complexity > 10)
- Poor naming (single letter vars, misleading names, abbreviations)
- Missing or inadequate error handling (bare except, swallowed exceptions)
- Magic numbers/strings (hardcoded values without named constants)
- Dead code (unreachable code, unused variables/imports/functions)
- Missing null/undefined checks (NPE risks)
- Overly nested code (deep if/else chains)
- Missing docstrings/comments on public APIs
- Functions with too many parameters (> 5 usually)
- Mutable default arguments in Python
- Missing type hints/annotations

Return ONLY a JSON object (no markdown, no preamble):
{
  "issues": [
    {
      "title": "Short issue title",
      "description": "Detailed explanation of why this is a problem",
      "severity": "critical|high|medium|low|info",
      "file_path": "path/to/file.py",
      "line_start": 42,
      "suggestion": "Specific improvement recommendation",
      "code_snippet": "the problematic code"
    }
  ],
  "summary": "One sentence summary of code quality findings"
}

If no issues: {"issues": [], "summary": "Code quality looks good."}"""


async def run_quality_agent(
    files: list[dict],
    pr_metadata: dict,
    on_issue: Optional[Callable] = None,
) -> AgentResult:
    start = time.time()

    code_context = f"PR: {pr_metadata.get('title', 'N/A')}\n\n"
    for f in files[:20]:
        if f.get("patch"):
            code_context += f"=== {f['filename']} ===\n{f['patch']}\n\n"

    if len(code_context) > 80000:
        code_context = code_context[:80000] + "\n... [truncated]"

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=QUALITY_SYSTEM_PROMPT,
    )
    response = await model.generate_content_async(
        f"Review this code for quality issues:\n\n{code_context}"
    )

    raw = response.text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)
    issues = []
    for i in data.get("issues", []):
        issue = ReviewIssue(
            category=IssueCategory.QUALITY,
            severity=Severity(i.get("severity", "low")),
            title=i["title"],
            description=i["description"],
            file_path=i.get("file_path", "unknown"),
            line_start=i.get("line_start"),
            suggestion=i.get("suggestion", ""),
            code_snippet=i.get("code_snippet"),
        )
        issues.append(issue)
        if on_issue:
            on_issue(issue)

    elapsed = int((time.time() - start) * 1000)
    return AgentResult(
        agent_name="Quality Agent",
        issues=issues,
        summary=data.get("summary", ""),
        execution_time_ms=elapsed,
    )
