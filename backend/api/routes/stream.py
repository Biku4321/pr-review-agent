"""
Server-Sent Events (SSE) streaming endpoint.
Clients connect and receive real-time agent events as a review runs.
"""
import asyncio
import json
import time
from typing import AsyncGenerator, Dict, List
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/stream", tags=["streaming"])

# In-memory event bus: review_id -> list of subscribers (asyncio.Queue)
_subscribers: Dict[str, List[asyncio.Queue]] = {}


def get_or_create_channel(review_id: str) -> None:
    if review_id not in _subscribers:
        _subscribers[review_id] = []


async def publish_event(review_id: str, event_type: str, data: dict) -> None:
    """Called by agents to broadcast an event to all SSE subscribers."""
    if review_id not in _subscribers:
        return
    payload = json.dumps({"type": event_type, "data": data, "ts": time.time()})
    dead = []
    for q in _subscribers[review_id]:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        try:
            _subscribers[review_id].remove(q)
        except ValueError:
            pass


async def _event_generator(review_id: str) -> AsyncGenerator[str, None]:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    get_or_create_channel(review_id)
    _subscribers[review_id].append(q)

    # Send a connected ping immediately
    yield f"data: {json.dumps({'type': 'connected', 'review_id': review_id})}\n\n"

    try:
        while True:
            try:
                payload = await asyncio.wait_for(q.get(), timeout=30.0)
                yield f"data: {payload}\n\n"

                # Stop streaming after review completes or fails
                parsed = json.loads(payload)
                if parsed.get("type") in ("review_completed", "review_failed"):
                    break
            except asyncio.TimeoutError:
                # Send keepalive comment
                yield ": keepalive\n\n"
    finally:
        try:
            _subscribers[review_id].remove(q)
        except ValueError:
            pass
        if review_id in _subscribers and not _subscribers[review_id]:
            del _subscribers[review_id]


@router.get("/{review_id}")
async def stream_review(review_id: str):
    """SSE endpoint. Connect to get real-time agent events for a review."""
    return StreamingResponse(
        _event_generator(review_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Event type constants (used by orchestrator) ───────────────────────────────
class EventType:
    REVIEW_STARTED = "review_started"
    AGENT_STARTED = "agent_started"
    AGENT_ISSUE_FOUND = "agent_issue_found"
    AGENT_COMPLETED = "agent_completed"
    SYNTHESIZING = "synthesizing"
    REVIEW_COMPLETED = "review_completed"
    REVIEW_FAILED = "review_failed"
