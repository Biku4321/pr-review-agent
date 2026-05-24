from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import get_db, ReviewRecord
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Overall stats for the analytics dashboard."""
    result = await db.execute(select(ReviewRecord))
    records = result.scalars().all()

    completed = [r for r in records if r.status == "completed"]

    category_counts = {"security": 0, "performance": 0, "quality": 0, "bug": 0}
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    total_issues = 0

    for r in completed:
        if r.agent_results:
            for issue in r.agent_results.get("issues", []):
                total_issues += 1
                cat = issue.get("category", "quality")
                sev = issue.get("severity", "low")
                if cat in category_counts:
                    category_counts[cat] += 1
                if sev in severity_counts:
                    severity_counts[sev] += 1

    avg_issues = round(total_issues / len(completed), 1) if completed else 0
    critical_pct = round(severity_counts["critical"] / total_issues * 100, 1) if total_issues else 0

    return {
        "total_reviews": len(records),
        "completed_reviews": len(completed),
        "total_issues_found": total_issues,
        "avg_issues_per_pr": avg_issues,
        "critical_percentage": critical_pct,
        "category_breakdown": category_counts,
        "severity_breakdown": severity_counts,
    }


@router.get("/trend")
async def get_trend(days: int = 14, db: AsyncSession = Depends(get_db)):
    """Daily issue counts for the trend chart."""
    result = await db.execute(
        select(ReviewRecord).where(
            ReviewRecord.status == "completed",
            ReviewRecord.created_at >= datetime.utcnow() - timedelta(days=days)
        ).order_by(ReviewRecord.created_at)
    )
    records = result.scalars().all()

    # Build day buckets
    buckets: dict = {}
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%m/%d")
        buckets[day] = {"date": day, "reviews": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "total_issues": 0}

    for r in records:
        day = r.created_at.strftime("%m/%d")
        if day in buckets:
            buckets[day]["reviews"] += 1
            buckets[day]["critical"] += r.critical_count or 0
            buckets[day]["high"] += r.high_count or 0
            buckets[day]["medium"] += r.medium_count or 0
            buckets[day]["low"] += r.low_count or 0
            buckets[day]["total_issues"] += r.total_issues or 0

    return list(buckets.values())


@router.get("/top-files")
async def get_top_files(db: AsyncSession = Depends(get_db)):
    """Files with the most issues across all reviews."""
    result = await db.execute(
        select(ReviewRecord).where(ReviewRecord.status == "completed")
    )
    records = result.scalars().all()

    file_issues: dict = {}
    for r in records:
        if r.agent_results:
            for issue in r.agent_results.get("issues", []):
                fp = issue.get("file_path", "unknown")
                if fp not in file_issues:
                    file_issues[fp] = {"file": fp, "total": 0, "critical": 0}
                file_issues[fp]["total"] += 1
                if issue.get("severity") == "critical":
                    file_issues[fp]["critical"] += 1

    top = sorted(file_issues.values(), key=lambda x: x["total"], reverse=True)[:10]
    return top
