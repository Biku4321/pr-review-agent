import asyncio
import time
import os
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
import google.generativeai as genai

from agents.security_agent import run_security_agent
from agents.performance_agent import run_performance_agent
from agents.quality_agent import run_quality_agent
from models.schemas import AgentResult, ReviewIssue

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


class ReviewState(TypedDict):
    repo: str
    pr_number: int
    review_id: str
    files: List[dict]
    pr_metadata: dict
    security_result: Optional[AgentResult]
    performance_result: Optional[AgentResult]
    quality_result: Optional[AgentResult]
    all_issues: List[ReviewIssue]
    overall_summary: str
    total_time_ms: int
    error: Optional[str]


async def _publish(review_id: str, event_type: str, data: dict):
    try:
        from api.routes.stream import publish_event
        await publish_event(review_id, event_type, data)
    except Exception:
        pass


async def fetch_data_node(state: ReviewState) -> ReviewState:
    await _publish(state["review_id"], "review_started", {
        "repo": state["repo"],
        "pr_number": state["pr_number"],
        "files_count": len(state["files"]),
    })
    return state


async def security_node(state: ReviewState) -> ReviewState:
    rid = state["review_id"]
    await _publish(rid, "agent_started", {"agent": "Security Agent", "icon": "🔒"})
    try:
        result = await run_security_agent(
            state["files"], state["pr_metadata"],
            on_issue=lambda issue: asyncio.create_task(
                _publish(rid, "agent_issue_found", {
                    "agent": "Security Agent",
                    "title": issue.title,
                    "severity": issue.severity.value,
                    "file_path": issue.file_path,
                })
            )
        )
        await _publish(rid, "agent_completed", {
            "agent": "Security Agent",
            "issues_count": len(result.issues),
            "summary": result.summary,
            "execution_time_ms": result.execution_time_ms,
        })
        return {**state, "security_result": result}
    except Exception as e:
        await _publish(rid, "agent_completed", {"agent": "Security Agent", "error": str(e)})
        return {**state, "security_result": AgentResult(
            agent_name="Security Agent", issues=[], summary=f"Error: {e}", execution_time_ms=0
        )}


async def performance_node(state: ReviewState) -> ReviewState:
    rid = state["review_id"]
    await _publish(rid, "agent_started", {"agent": "Performance Agent", "icon": "⚡"})
    try:
        result = await run_performance_agent(
            state["files"], state["pr_metadata"],
            on_issue=lambda issue: asyncio.create_task(
                _publish(rid, "agent_issue_found", {
                    "agent": "Performance Agent",
                    "title": issue.title,
                    "severity": issue.severity.value,
                    "file_path": issue.file_path,
                })
            )
        )
        await _publish(rid, "agent_completed", {
            "agent": "Performance Agent",
            "issues_count": len(result.issues),
            "summary": result.summary,
            "execution_time_ms": result.execution_time_ms,
        })
        return {**state, "performance_result": result}
    except Exception as e:
        await _publish(rid, "agent_completed", {"agent": "Performance Agent", "error": str(e)})
        return {**state, "performance_result": AgentResult(
            agent_name="Performance Agent", issues=[], summary=f"Error: {e}", execution_time_ms=0
        )}


async def quality_node(state: ReviewState) -> ReviewState:
    rid = state["review_id"]
    await _publish(rid, "agent_started", {"agent": "Quality Agent", "icon": "🧹"})
    try:
        result = await run_quality_agent(
            state["files"], state["pr_metadata"],
            on_issue=lambda issue: asyncio.create_task(
                _publish(rid, "agent_issue_found", {
                    "agent": "Quality Agent",
                    "title": issue.title,
                    "severity": issue.severity.value,
                    "file_path": issue.file_path,
                })
            )
        )
        await _publish(rid, "agent_completed", {
            "agent": "Quality Agent",
            "issues_count": len(result.issues),
            "summary": result.summary,
            "execution_time_ms": result.execution_time_ms,
        })
        return {**state, "quality_result": result}
    except Exception as e:
        await _publish(rid, "agent_completed", {"agent": "Quality Agent", "error": str(e)})
        return {**state, "quality_result": AgentResult(
            agent_name="Quality Agent", issues=[], summary=f"Error: {e}", execution_time_ms=0
        )}


async def synthesize_node(state: ReviewState) -> ReviewState:
    rid = state["review_id"]
    await _publish(rid, "synthesizing", {"message": "Generating executive summary..."})

    all_issues: List[ReviewIssue] = []
    for key in ["security_result", "performance_result", "quality_result"]:
        result = state.get(key)
        if result:
            all_issues.extend(result.issues)

    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    all_issues.sort(key=lambda x: sev_order.get(x.severity.value, 5))

    summaries = []
    for key in ["security_result", "performance_result", "quality_result"]:
        r = state.get(key)
        if r:
            summaries.append(f"{r.agent_name}: {r.summary} ({len(r.issues)} issues)")

    prompt = f"""PR: {state['pr_metadata'].get('title', 'N/A')}
Agent findings:
{chr(10).join(summaries)}

Total issues: {len(all_issues)}
Critical: {sum(1 for i in all_issues if i.severity.value == 'critical')}
High: {sum(1 for i in all_issues if i.severity.value == 'high')}

Write a 2-3 sentence executive summary. Be direct and actionable. No markdown."""

    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    response = await model.generate_content_async(prompt)
    summary = response.text.strip()

    await _publish(rid, "review_completed", {
        "total_issues": len(all_issues),
        "critical": sum(1 for i in all_issues if i.severity.value == "critical"),
        "high": sum(1 for i in all_issues if i.severity.value == "high"),
        "summary": summary,
    })

    return {**state, "all_issues": all_issues, "overall_summary": summary}


def build_review_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("fetch_data", fetch_data_node)
    graph.add_node("security", security_node)
    graph.add_node("performance", performance_node)
    graph.add_node("quality", quality_node)
    graph.add_node("synthesize", synthesize_node)
    graph.set_entry_point("fetch_data")
    graph.add_edge("fetch_data", "security")
    graph.add_edge("fetch_data", "performance")
    graph.add_edge("fetch_data", "quality")
    graph.add_edge("security", "synthesize")
    graph.add_edge("performance", "synthesize")
    graph.add_edge("quality", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


async def run_review(
    repo: str,
    pr_number: int,
    files: List[dict],
    pr_metadata: dict,
    review_id: str = "",
) -> ReviewState:
    graph = build_review_graph()
    start = time.time()

    initial_state: ReviewState = {
        "repo": repo,
        "pr_number": pr_number,
        "review_id": review_id,
        "files": files,
        "pr_metadata": pr_metadata,
        "security_result": None,
        "performance_result": None,
        "quality_result": None,
        "all_issues": [],
        "overall_summary": "",
        "total_time_ms": 0,
        "error": None,
    }

    final_state = await graph.ainvoke(initial_state)
    final_state["total_time_ms"] = int((time.time() - start) * 1000)
    return final_state
