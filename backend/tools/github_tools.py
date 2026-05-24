import os
from github import Github, GithubException
from typing import Optional
import httpx


def get_github_client(token: Optional[str] = None) -> Github:
    t = token or os.getenv("GITHUB_TOKEN")
    return Github(t)


def get_pr_diff(repo_full_name: str, pr_number: int, token: Optional[str] = None) -> str:
    """Fetch the raw diff of a pull request."""
    g = get_github_client(token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    headers = {
        "Authorization": f"token {token or os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3.diff",
    }
    import requests
    resp = requests.get(pr.url, headers=headers)
    resp.raise_for_status()
    return resp.text


def get_pr_files(repo_full_name: str, pr_number: int, token: Optional[str] = None) -> list[dict]:
    """Get list of changed files with patch content."""
    g = get_github_client(token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    files = []
    for f in pr.get_files():
        files.append({
            "filename": f.filename,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
            "patch": f.patch or "",
            "raw_url": f.raw_url,
        })
    return files


def get_pr_metadata(repo_full_name: str, pr_number: int, token: Optional[str] = None) -> dict:
    """Get PR title, description, author, base/head branch."""
    g = get_github_client(token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    return {
        "title": pr.title,
        "body": pr.body or "",
        "author": pr.user.login,
        "base_branch": pr.base.ref,
        "head_branch": pr.head.ref,
        "url": pr.html_url,
        "additions": pr.additions,
        "deletions": pr.deletions,
        "changed_files": pr.changed_files,
    }


def post_review_comment(
    repo_full_name: str,
    pr_number: int,
    body: str,
    token: Optional[str] = None
) -> str:
    """Post a review comment on a PR. Returns comment URL."""
    g = get_github_client(token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    comment = pr.create_issue_comment(body)
    return comment.html_url


def format_review_as_markdown(issues: list[dict], summary: str) -> str:
    """Format agent review results as a clean GitHub markdown comment."""
    severity_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
        "info": "⚪",
    }
    category_emoji = {
        "security": "🔒",
        "performance": "⚡",
        "quality": "🧹",
        "bug": "🐛",
    }

    lines = [
        "## 🤖 AI Code Review",
        "",
        f"**Summary:** {summary}",
        "",
    ]

    if not issues:
        lines.append("✅ No issues found. Looks good!")
        return "\n".join(lines)

    # Group by severity
    by_severity = {}
    for issue in issues:
        s = issue.get("severity", "info")
        by_severity.setdefault(s, []).append(issue)

    counts = {s: len(v) for s, v in by_severity.items()}
    badge_parts = []
    for sev in ["critical", "high", "medium", "low"]:
        if counts.get(sev):
            badge_parts.append(f"{severity_emoji[sev]} {sev.capitalize()}: {counts[sev]}")
    lines.append(" | ".join(badge_parts))
    lines.append("")

    for sev in ["critical", "high", "medium", "low", "info"]:
        if sev not in by_severity:
            continue
        for issue in by_severity[sev]:
            cat = issue.get("category", "quality")
            lines.append(f"### {severity_emoji[sev]} {category_emoji.get(cat, '')} {issue['title']}")
            lines.append(f"**File:** `{issue['file_path']}`")
            if issue.get("line_start"):
                lines.append(f"**Line:** {issue['line_start']}")
            lines.append(f"**Category:** {cat.capitalize()} | **Severity:** {sev.capitalize()}")
            lines.append("")
            lines.append(issue["description"])
            lines.append("")
            if issue.get("suggestion"):
                lines.append(f"💡 **Suggestion:** {issue['suggestion']}")
            if issue.get("code_snippet"):
                lines.append(f"```\n{issue['code_snippet']}\n```")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.append("*Powered by AI Code Review Agent 🚀*")
    return "\n".join(lines)
