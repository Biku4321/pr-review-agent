import time
import json
import re
import os
from typing import Callable, Optional
import google.generativeai as genai
from models.schemas import AgentResult, ReviewIssue, Severity, IssueCategory
from rag.knowledge_base import get_relevant_context

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

SECURITY_SYSTEM_PROMPT = """You are an expert security code reviewer with deep knowledge of OWASP Top 10, CVEs, and secure coding practices.

You will be given:
1. Code changes from a pull request
2. A KNOWLEDGE BASE of relevant vulnerability patterns retrieved via RAG (use these as reference)

Your job: find ALL security vulnerabilities. Reference the knowledge base entries (by ID like OWASP-A03-001) when applicable.

Focus areas:
- SQL/NoSQL injection, Command injection, XSS
- Hardcoded secrets, API keys, JWT issues
- Authentication/authorization flaws (missing checks, IDOR)
- Insecure deserialization (pickle, yaml.load)
- Path traversal, SSRF
- Weak cryptography (MD5/SHA1 passwords, hardcoded keys)
- Missing input validation, sensitive data in logs
- OWASP Top 10 (A01-A10 2021)

Return ONLY a JSON object (no markdown, no preamble):
{
  "issues": [
    {
      "title": "Short issue title",
      "description": "Detailed explanation with CWE/OWASP reference if applicable",
      "severity": "critical|high|medium|low|info",
      "file_path": "path/to/file.py",
      "line_start": 42,
      "suggestion": "Specific fix with corrected code example",
      "code_snippet": "the vulnerable code line(s)",
      "owasp_id": "OWASP-A03-001 or CWE-89 etc"
    }
  ],
  "summary": "One sentence executive summary of security findings"
}

If no security issues: {"issues": [], "summary": "No security issues detected."}"""


async def run_security_agent(
    files: list[dict],
    pr_metadata: dict,
    on_issue: Optional[Callable] = None,
) -> AgentResult:
    start = time.time()

    code_context = f"PR: {pr_metadata.get('title', 'N/A')}\n\n"
    all_code = ""
    for f in files[:20]:
        if f.get("patch") and any(f["filename"].endswith(ext) for ext in
                                   [".py", ".js", ".ts", ".java", ".go", ".rb", ".php", ".cs", ".cpp", ".c"]):
            patch = f["patch"]
            code_context += f"=== {f['filename']} ===\n{patch}\n\n"
            all_code += patch + "\n"

    rag_context = get_relevant_context(all_code, category="security", top_k=6)
    if len(code_context) > 70000:
        code_context = code_context[:70000] + "\n... [truncated]"

    user_message = f"{rag_context}\n\n---\n\n## Code to Review\n\n{code_context}"

    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        system_instruction=SECURITY_SYSTEM_PROMPT,
    )
    response = await model.generate_content_async(user_message)

    raw = response.text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)
    issues = []
    for i in data.get("issues", []):
        issue = ReviewIssue(
            category=IssueCategory.SECURITY,
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
        agent_name="Security Agent",
        issues=issues,
        summary=data.get("summary", ""),
        execution_time_ms=elapsed,
    )
