import time
import json
import re
import os
from typing import Callable, Optional
import google.generativeai as genai
from models.schemas import AgentResult, ReviewIssue, Severity, IssueCategory

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

PERFORMANCE_SYSTEM_PROMPT = """You are an expert performance engineering code reviewer. Your ONLY job is to find performance issues.

Focus on:
- N+1 query problems (queries inside loops, missing eager loading)
- Missing database indexes on frequently queried columns
- Inefficient algorithms (O(n²) where O(n log n) is possible)
- Memory leaks (unclosed resources, unbounded caches, circular references)
- Blocking I/O in async code (synchronous calls in async functions)
- Unnecessary re-renders in React/Vue (missing memoization, deps arrays)
- Large data fetched when only subset needed (SELECT * vs specific columns)
- Missing pagination on list endpoints
- Redundant/duplicate API calls or computations
- Synchronous file/network operations in hot paths

Return ONLY a JSON object (no markdown, no preamble):
{
  "issues": [
    {
      "title": "Short issue title",
      "description": "Detailed explanation and performance impact",
      "severity": "critical|high|medium|low|info",
      "file_path": "path/to/file.py",
      "line_start": 42,
      "suggestion": "Specific optimization recommendation with example",
      "code_snippet": "the problematic code"
    }
  ],
  "summary": "One sentence summary of performance findings"
}

If no issues: {"issues": [], "summary": "No significant performance issues detected."}"""


async def run_performance_agent(
    files: list[dict],
    pr_metadata: dict,
    on_issue: Optional[Callable] = None,
) -> AgentResult:
    start = time.time()

    code_context = f"PR: {pr_metadata.get('title', 'N/A')}\n\n"
    for f in files[:20]:
        if f.get("patch") and any(f["filename"].endswith(ext) for ext in
                                   [".py", ".js", ".ts", ".java", ".go", ".rb", ".php",
                                    ".tsx", ".jsx", ".sql", ".cs"]):
            code_context += f"=== {f['filename']} ===\n{f['patch']}\n\n"

    if len(code_context) > 80000:
        code_context = code_context[:80000] + "\n... [truncated]"

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=PERFORMANCE_SYSTEM_PROMPT,
    )
    response = await model.generate_content_async(
        f"Review this code for performance issues:\n\n{code_context}"
    )

    raw = response.text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)
    issues = []
    for i in data.get("issues", []):
        issue = ReviewIssue(
            category=IssueCategory.PERFORMANCE,
            severity=Severity(i.get("severity", "medium")),
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
        agent_name="Performance Agent",
        issues=issues,
        summary=data.get("summary", ""),
        execution_time_ms=elapsed,
    )
