from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from models.schemas import ReviewRequest, ReviewResponse, ReviewListItem
from api.review_service import create_review, get_review, list_reviews

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=202)
async def start_review(req: ReviewRequest, db: AsyncSession = Depends(get_db)):
    return await create_review(db, req.repo_full_name, req.pr_number, req.github_token)


@router.get("", response_model=list[ReviewListItem])
async def get_reviews(limit: int = 20, db: AsyncSession = Depends(get_db)):
    return await list_reviews(db, limit)


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review_by_id(review_id: str, db: AsyncSession = Depends(get_db)):
    review = await get_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
