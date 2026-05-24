from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    BUG = "bug"


class ReviewIssue(BaseModel):
    category: IssueCategory
    severity: Severity
    title: str
    description: str
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    suggestion: str
    code_snippet: Optional[str] = None


class AgentResult(BaseModel):
    agent_name: str
    issues: List[ReviewIssue] = []
    summary: str
    execution_time_ms: int


class ReviewStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewRequest(BaseModel):
    repo_full_name: str = Field(..., example="owner/repo")
    pr_number: int = Field(..., example=42)
    github_token: Optional[str] = None


class ReviewResponse(BaseModel):
    review_id: str
    status: ReviewStatus
    repo: str
    pr_number: int
    pr_title: Optional[str] = None
    pr_url: Optional[str] = None
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    agent_results: List[AgentResult] = []
    overall_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ReviewListItem(BaseModel):
    review_id: str
    status: ReviewStatus
    repo: str
    pr_number: int
    pr_title: Optional[str]
    total_issues: int
    critical_count: int
    created_at: datetime


class WebhookPayload(BaseModel):
    action: str
    number: Optional[int] = None
    pull_request: Optional[dict] = None
    repository: Optional[dict] = None
