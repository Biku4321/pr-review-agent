from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from db.database import init_db
from api.routes.reviews import router as reviews_router
from api.routes.webhook import router as webhook_router
from api.routes.stream import router as stream_router
from api.routes.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PR Review Agent",
    description="AI-powered multi-agent code review system",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews_router)
app.include_router(webhook_router)
app.include_router(stream_router)
app.include_router(analytics_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "pr-review-agent", "version": "2.0.0"}
