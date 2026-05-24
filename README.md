# ⬡ PR Review Agent

> AI-powered multi-agent code review system. Three specialist agents (Security, Performance, Quality) run in parallel via LangGraph, review any GitHub PR in under 60 seconds, and post structured comments automatically.

---

## Architecture

```
GitHub Webhook / API Request
         │
         ▼
   FastAPI Backend
         │
         ▼
  LangGraph Orchestrator
   ┌──────┴──────┐──────────────┐
   ▼             ▼              ▼
Security      Performance    Quality
 Agent          Agent         Agent
   │             │              │
   └──────────────┴──────────────┘
                 │
                 ▼
          Synthesize Node
         (executive summary)
                 │
          ┌──────┴──────┐
          ▼             ▼
     PostgreSQL    GitHub PR Comment
     (history)
```

**Stack:**
- **Agent Framework:** LangGraph + LangChain
- **LLM:** Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- **Backend:** FastAPI + asyncio (Python 3.12)
- **Frontend:** Next.js 14 + Tailwind CSS
- **DB:** PostgreSQL + Redis
- **GitHub:** PyGithub + Webhooks

---

## Quick Start

### 1. Clone & configure
```bash
git clone https://github.com/your-org/pr-review-agent
cd pr-review-agent
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY and GITHUB_TOKEN
```

### 2. Run with Docker (recommended)
```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Run locally (development)
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### 4. Test without GitHub
```bash
cd backend
python test_local.py
```

---

## Usage

### Via UI
1. Open http://localhost:3000
2. Enter `owner/repo` and PR number
3. Watch agents run in real-time
4. See issues by category and severity

### Via API
```bash
curl -X POST http://localhost:8000/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"repo_full_name": "owner/repo", "pr_number": 42}'
```

### Via GitHub Webhook
1. Go to your repo Settings → Webhooks → Add webhook
2. URL: `https://your-domain.com/webhook/github`
3. Content type: `application/json`
4. Events: `Pull requests`

The agent auto-triggers on every PR open/update and posts a review comment.

---

## What the Agents Find

| Agent | Detects |
|-------|---------|
| 🔒 Security | SQL injection, XSS, hardcoded secrets, path traversal, weak crypto, OWASP Top 10 |
| ⚡ Performance | N+1 queries, missing indexes, blocking async calls, memory leaks, inefficient algorithms |
| 🧹 Quality | DRY violations, dead code, poor naming, missing error handling, magic numbers, complexity |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GITHUB_TOKEN` | GitHub personal access token (repo scope) |
| `GITHUB_WEBHOOK_SECRET` | Webhook verification secret |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |

---

## Project Structure

```
pr-review-agent/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py     # LangGraph supervisor graph
│   │   ├── security_agent.py   # OWASP / CVE specialist
│   │   ├── performance_agent.py
│   │   └── quality_agent.py
│   ├── tools/
│   │   └── github_tools.py     # PR fetch + comment posting
│   ├── api/
│   │   ├── main.py             # FastAPI app
│   │   ├── review_service.py   # Business logic
│   │   └── routes/
│   │       ├── reviews.py
│   │       └── webhook.py
│   ├── models/schemas.py
│   ├── db/database.py
│   └── test_local.py
├── frontend/
│   └── app/
│       ├── dashboard/          # Review list + metrics
│       └── review/[id]/        # Live agent trace + issues
├── docker-compose.yml
└── .env.example
```
