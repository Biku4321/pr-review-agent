import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from db.database import ReviewRecord
from models.schemas import ReviewResponse, ReviewListItem, ReviewStatus, AgentResult
from agents.orchestrator import run_review
from tools.github_tools import get_pr_files, get_pr_metadata, post_review_comment, format_review_as_markdown
import asyncio


async def create_review(
    db: AsyncSession,
    repo: str,
    pr_number: int,
    github_token: Optional[str] = None,
) -> ReviewResponse:
    review_id = str(uuid.uuid4())[:8]

    # Create pending record
    record = ReviewRecord(
        review_id=review_id,
        status="pending",
        repo=repo,
        pr_number=pr_number,
    )
    db.add(record)
    await db.commit()

    # Run review in background
    asyncio.create_task(
        _run_review_background(db, review_id, repo, pr_number, github_token)
    )

    return ReviewResponse(
        review_id=review_id,
        status=ReviewStatus.PENDING,
        repo=repo,
        pr_number=pr_number,
    )


async def _run_review_background(
    db: AsyncSession,
    review_id: str,
    repo: str,
    pr_number: int,
    github_token: Optional[str],
):
    from db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            # Mark running
            result = await session.execute(select(ReviewRecord).where(ReviewRecord.review_id == review_id))
            record = result.scalar_one()
            record.status = "running"
            await session.commit()

            # Fetch PR data
            files = get_pr_files(repo, pr_number, github_token)
            metadata = get_pr_metadata(repo, pr_number, github_token)
            record.pr_title = metadata.get("title")
            record.pr_url = metadata.get("url")
            await session.commit()

            # Run multi-agent review
            state = await run_review(repo, pr_number, files, metadata, review_id=review_id)

            # Count issues by severity
            issues = state.get("all_issues", [])
            issue_dicts = [i.model_dump() for i in issues]
            # Convert enums to strings for JSON storage
            for d in issue_dicts:
                d["severity"] = d["severity"].value if hasattr(d["severity"], "value") else d["severity"]
                d["category"] = d["category"].value if hasattr(d["category"], "value") else d["category"]

            agent_results_data = []
            for key in ["security_result", "performance_result", "quality_result"]:
                r: AgentResult = state.get(key)
                if r:
                    agent_results_data.append({
                        "agent_name": r.agent_name,
                        "summary": r.summary,
                        "execution_time_ms": r.execution_time_ms,
                        "issues_count": len(r.issues),
                    })

            record.status = "completed"
            record.total_issues = len(issues)
            record.critical_count = sum(1 for i in issues if i.severity.value == "critical")
            record.high_count = sum(1 for i in issues if i.severity.value == "high")
            record.medium_count = sum(1 for i in issues if i.severity.value == "medium")
            record.low_count = sum(1 for i in issues if i.severity.value == "low")
            record.agent_results = {
                "agent_summaries": agent_results_data,
                "issues": issue_dicts,
            }
            record.overall_summary = state.get("overall_summary", "")
            record.completed_at = datetime.utcnow()
            await session.commit()

            # Post to GitHub
            try:
                md = format_review_as_markdown(issue_dicts, record.overall_summary)
                post_review_comment(repo, pr_number, md, github_token)
            except Exception:
                pass  # Don't fail review if GitHub comment fails

        except Exception as e:
            result = await session.execute(select(ReviewRecord).where(ReviewRecord.review_id == review_id))
            record = result.scalar_one_or_none()
            if record:
                record.status = "failed"
                record.error = str(e)
                record.completed_at = datetime.utcnow()
                await session.commit()


async def get_review(db: AsyncSession, review_id: str) -> Optional[ReviewResponse]:
    result = await db.execute(select(ReviewRecord).where(ReviewRecord.review_id == review_id))
    record = result.scalar_one_or_none()
    if not record:
        return None
    return _record_to_response(record)


async def list_reviews(db: AsyncSession, limit: int = 20) -> list[ReviewListItem]:
    result = await db.execute(
        select(ReviewRecord).order_by(desc(ReviewRecord.created_at)).limit(limit)
    )
    records = result.scalars().all()
    return [
        ReviewListItem(
            review_id=r.review_id,
            status=ReviewStatus(r.status),
            repo=r.repo,
            pr_number=r.pr_number,
            pr_title=r.pr_title,
            total_issues=r.total_issues,
            critical_count=r.critical_count,
            created_at=r.created_at,
        )
        for r in records
    ]


def _record_to_response(record: ReviewRecord) -> ReviewResponse:
    from models.schemas import AgentResult, ReviewIssue, Severity, IssueCategory
    agent_results = []
    issues_data = []

    if record.agent_results:
        for a in record.agent_results.get("agent_summaries", []):
            agent_results.append(AgentResult(
                agent_name=a["agent_name"],
                issues=[],
                summary=a["summary"],
                execution_time_ms=a["execution_time_ms"],
            ))
        for i in record.agent_results.get("issues", []):
            try:
                issues_data.append(ReviewIssue(
                    category=IssueCategory(i["category"]),
                    severity=Severity(i["severity"]),
                    title=i["title"],
                    description=i["description"],
                    file_path=i["file_path"],
                    line_start=i.get("line_start"),
                    suggestion=i.get("suggestion", ""),
                    code_snippet=i.get("code_snippet"),
                ))
            except Exception:
                pass

    # Attach issues to last agent result for response
    if agent_results:
        agent_results[-1].issues = issues_data

    return ReviewResponse(
        review_id=record.review_id,
        status=ReviewStatus(record.status),
        repo=record.repo,
        pr_number=record.pr_number,
        pr_title=record.pr_title,
        pr_url=record.pr_url,
        total_issues=record.total_issues,
        critical_count=record.critical_count,
        high_count=record.high_count,
        medium_count=record.medium_count,
        low_count=record.low_count,
        agent_results=agent_results,
        overall_summary=record.overall_summary,
        created_at=record.created_at,
        completed_at=record.completed_at,
        error=record.error,
    )
