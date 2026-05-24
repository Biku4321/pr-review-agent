"use client";
import { useEffect, useRef, useState } from "react";
import { getReview, createSSEConnection } from "../../../lib/api";
import Link from "next/link";

const SEV_STYLE: Record<string, string> = {
  critical: "text-red-400 border-red-400/40 bg-red-400/10",
  high: "text-orange-400 border-orange-400/40 bg-orange-400/10",
  medium: "text-yellow-400 border-yellow-400/40 bg-yellow-400/10",
  low: "text-blue-400 border-blue-400/40 bg-blue-400/10",
  info: "text-gray-400 border-gray-400/40 bg-gray-400/10",
};
const SEV_DOT: Record<string, string> = {
  critical: "bg-red-400",
  high: "bg-orange-400",
  medium: "bg-yellow-400",
  low: "bg-blue-400",
  info: "bg-gray-400",
};
const CAT_ICON: Record<string, string> = {
  security: "🔒",
  performance: "⚡",
  quality: "🧹",
  bug: "🐛",
};

type LiveEvent = {
  id: number;
  type: string;
  agent?: string;
  title?: string;
  severity?: string;
  file?: string;
  message?: string;
  ts: number;
};

function AgentCard({
  name,
  icon,
  state,
}: {
  name: string;
  icon: string;
  state: "idle" | "running" | "done";
  result?: any;
}) {
  const isRunning = state === "running";
  const isDone = state === "done";
  return (
    <div
      className={`bg-[#111827] border rounded-lg p-4 transition-all duration-700 ${
        isRunning
          ? "border-cyan-400/50 shadow-[0_0_20px_rgba(34,211,238,0.1)]"
          : isDone && result?.issues_count > 0
            ? "border-red-400/30"
            : isDone
              ? "border-emerald-400/30"
              : "border-gray-800"
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-base">{icon}</span>
        <span className="font-mono text-sm font-semibold text-gray-200">
          {name}
        </span>
        <div className="ml-auto flex items-center gap-1.5">
          {isRunning && (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-xs font-mono text-cyan-400">
                analyzing...
              </span>
            </>
          )}
          {isDone && (
            <span
              className={`text-xs font-mono ${(result?.issues_count ?? 0) > 0 ? "text-red-400" : "text-emerald-400"}`}
            >
              {(result?.issues_count ?? 0) > 0
                ? `${result.issues_count} issues`
                : "✓ clean"}
            </span>
          )}
          {state === "idle" && (
            <span className="text-xs font-mono text-gray-600">waiting</span>
          )}
        </div>
      </div>
      {isDone && result?.summary && (
        <p className="text-xs text-gray-500 font-mono leading-relaxed">
          {result.summary}
        </p>
      )}
      {isRunning && (
        <div className="h-0.5 bg-gray-800 rounded overflow-hidden mt-2">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 to-cyan-300 rounded animate-[shimmer_1.5s_ease-in-out_infinite]"
            style={{ width: "60%" }}
          />
        </div>
      )}
      {isDone && result?.execution_time_ms && (
        <div className="text-xs font-mono text-gray-600 mt-1">
          {result.execution_time_ms}ms
        </div>
      )}
    </div>
  );
}

export default function ReviewDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const [review, setReview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);
  const [agentStates, setAgentStates] = useState<
    Record<string, "idle" | "running" | "done">
  >({
    "Security Agent": "idle",
    "Performance Agent": "idle",
    "Quality Agent": "idle",
  });
  const [agentResults, setAgentResults] = useState<Record<string, any>>({});
  const [liveIssueCount, setLiveIssueCount] = useState(0);
  const eventRef = useRef<LiveEvent[]>([]);
  const counterRef = useRef(0);
  const logRef = useRef<HTMLDivElement>(null);

  const addEvent = (type: string, data: any) => {
    const ev: LiveEvent = {
      id: counterRef.current++,
      type,
      ts: Date.now(),
      ...data,
    };
    eventRef.current = [ev, ...eventRef.current].slice(0, 50);
    setLiveEvents([...eventRef.current]);
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = 0;
    }, 50);
  };

  useEffect(() => {
    let mounted = true;
    let sseCleanup: (() => void) | null = null;

    const init = async () => {
      try {
        const data = await getReview(params.id);
        if (!mounted) return;
        setReview(data);
        setLoading(false);

        if (data.status === "pending" || data.status === "running") {
          sseCleanup = createSSEConnection(params.id, (type, evData) => {
            addEvent(type, evData);

            if (type === "agent_started") {
              setAgentStates((p) => ({ ...p, [evData.agent]: "running" }));
            } else if (type === "agent_issue_found") {
              setLiveIssueCount((c) => c + 1);
            } else if (type === "agent_completed") {
              setAgentStates((p) => ({ ...p, [evData.agent]: "done" }));
              setAgentResults((p) => ({ ...p, [evData.agent]: evData }));
            } else if (
              type === "review_completed" ||
              type === "review_failed"
            ) {
              // Fetch final review state
              setTimeout(async () => {
                const final = await getReview(params.id);
                if (!mounted) return;
                setReview(final);
                setAgentStates({
                  "Security Agent": "done",
                  "Performance Agent": "done",
                  "Quality Agent": "done",
                });
              }, 800);
            }
          });
        } else if (data.status === "completed") {
          // Pre-populate agent states from completed data
          setAgentStates({
            "Security Agent": "done",
            "Performance Agent": "done",
            "Quality Agent": "done",
          });
          const ar: Record<string, any> = {};
          (data.agent_results || []).forEach((a: any) => {
            ar[a.agent_name] = a;
          });
          setAgentResults(ar);
        }
      } catch (e) {
        console.error(e);
        setLoading(false);
      }
    };

    init();
    return () => {
      mounted = false;
      sseCleanup?.();
    };
  }, [params.id, addEvent]);

  const isLive = review?.status === "pending" || review?.status === "running";
  const allIssues = (review?.agent_results || []).flatMap(
    (a: any) => a.issues || [],
  );
  const counts = { critical: 0, high: 0, medium: 0, low: 0 };
  allIssues.forEach((i: any) => {
    if (i.severity in counts) counts[i.severity as keyof typeof counts]++;
  });

  if (loading)
    return (
      <div className="text-center py-20 text-gray-600 font-mono text-sm">
        <div className="inline-block w-6 h-6 border-2 border-gray-700 border-t-cyan-400 rounded-full animate-spin mb-3" />
        <div>Connecting...</div>
      </div>
    );

  return (
    <div className="animate-[fadeIn_0.4s_ease-out]">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm font-mono text-gray-600 mb-6">
        <Link
          href="/dashboard"
          className="hover:text-gray-300 transition-colors"
        >
          dashboard
        </Link>
        <span>/</span>
        <span className="text-gray-300">review/{review?.review_id}</span>
      </div>

      {/* Header row */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-semibold tracking-tight font-mono">
              <span className="text-gray-400">{review?.repo}</span>
              <span className="text-cyan-400 ml-1">#{review?.pr_number}</span>
            </h1>
            <span
              className={`text-xs font-mono px-2 py-0.5 rounded border ${
                isLive
                  ? "text-cyan-400 border-cyan-400/30 bg-cyan-400/10"
                  : review?.status === "completed"
                    ? "text-emerald-400 border-emerald-400/30 bg-emerald-400/10"
                    : "text-red-400 border-red-400/30 bg-red-400/10"
              }`}
            >
              {review?.status}
            </span>
            {isLive && liveIssueCount > 0 && (
              <span className="text-xs font-mono text-red-400 animate-pulse">
                {liveIssueCount} issues found so far...
              </span>
            )}
          </div>
          {review?.pr_title && (
            <p className="text-gray-500 text-sm mt-1">{review.pr_title}</p>
          )}
          {review?.pr_url && (
            <a
              href={review.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-mono text-cyan-500 hover:underline mt-1 inline-block"
            >
              View on GitHub →
            </a>
          )}
        </div>
        {review?.status === "completed" && (
          <div className="text-right shrink-0">
            <div className="text-3xl font-mono font-semibold">
              {review.total_issues}
            </div>
            <div className="text-xs text-gray-600 font-mono">issues found</div>
          </div>
        )}
      </div>

      {/* Agent trace cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        <AgentCard
          name="Security Agent"
          icon="🔒"
          state={agentStates["Security Agent"]}
          result={
            agentResults["Security Agent"] ||
            review?.agent_results?.find(
              (a: any) => a.agent_name === "Security Agent",
            )
          }
        />
        <AgentCard
          name="Performance Agent"
          icon="⚡"
          state={agentStates["Performance Agent"]}
          result={
            agentResults["Performance Agent"] ||
            review?.agent_results?.find(
              (a: any) => a.agent_name === "Performance Agent",
            )
          }
        />
        <AgentCard
          name="Quality Agent"
          icon="🧹"
          state={agentStates["Quality Agent"]}
          result={
            agentResults["Quality Agent"] ||
            review?.agent_results?.find(
              (a: any) => a.agent_name === "Quality Agent",
            )
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Live event log */}
        {(isLive || liveEvents.length > 0) && (
          <div className="lg:col-span-1 bg-[#111827] border border-gray-800 rounded-lg overflow-hidden">
            <div className="px-3 py-2 border-b border-gray-800 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">
                Live event stream
              </span>
            </div>
            <div
              ref={logRef}
              className="p-3 h-64 overflow-y-auto space-y-1 font-mono text-xs"
            >
              {liveEvents.length === 0 && (
                <div className="text-gray-700">Waiting for events...</div>
              )}
              {liveEvents.map((ev) => (
                <div
                  key={ev.id}
                  className="flex items-start gap-2 animate-[fadeIn_0.2s_ease-out]"
                >
                  <span className="text-gray-700 shrink-0">
                    {new Date(ev.ts).toLocaleTimeString("en", {
                      hour12: false,
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </span>
                  {ev.type === "agent_started" && (
                    <span className="text-cyan-400">[{ev.agent}] started</span>
                  )}
                  {ev.type === "agent_issue_found" && (
                    <span>
                      <span
                        className={`${SEV_DOT[ev.severity || "info"]} inline-block w-1.5 h-1.5 rounded-full mr-1 -mb-0.5`}
                      />
                      <span className="text-gray-400">[{ev.agent}]</span>
                      <span className="text-gray-200 ml-1">{ev.title}</span>
                    </span>
                  )}
                  {ev.type === "agent_completed" && (
                    <span className="text-emerald-400">
                      [{ev.agent}] ✓ done
                    </span>
                  )}
                  {ev.type === "synthesizing" && (
                    <span className="text-yellow-400">
                      synthesizing results...
                    </span>
                  )}
                  {ev.type === "review_completed" && (
                    <span className="text-emerald-400 font-semibold">
                      ✓ review complete
                    </span>
                  )}
                  {ev.type === "review_started" && (
                    <span className="text-cyan-300">review started</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        {review?.overall_summary && (
          <div
            className={`${isLive && liveEvents.length > 0 ? "lg:col-span-2" : "lg:col-span-3"} bg-[#111827] border border-gray-800 rounded-lg p-4 flex flex-col justify-center`}
          >
            <div className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-2">
              Executive Summary
            </div>
            <p className="text-sm text-gray-200 leading-relaxed">
              {review.overall_summary}
            </p>
          </div>
        )}
      </div>

      {/* Severity counts */}
      {review?.status === "completed" && review?.total_issues > 0 && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          {(["critical", "high", "medium", "low"] as const).map((s) => (
            <div
              key={s}
              className="bg-[#111827] border border-gray-800 rounded-lg p-3 text-center"
            >
              <div
                className="text-2xl font-mono font-bold"
                style={{
                  color:
                    s === "critical"
                      ? "#f87171"
                      : s === "high"
                        ? "#fb923c"
                        : s === "medium"
                          ? "#fbbf24"
                          : "#60a5fa",
                }}
              >
                {counts[s]}
              </div>
              <div className="text-xs font-mono text-gray-600 capitalize mt-0.5">
                {s}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Issues list */}
      {allIssues.length > 0 && (
        <div className="bg-[#111827] border border-gray-800 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">
              Issues ({allIssues.length})
            </span>
          </div>
          <div className="divide-y divide-gray-900">
            {allIssues.map((issue: any, i: number) => (
              <div
                key={i}
                className="p-4 hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg mt-0.5 shrink-0">
                    {CAT_ICON[issue.category] || "❓"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <span className="font-mono text-sm font-semibold text-gray-100">
                        {issue.title}
                      </span>
                      <span
                        className={`text-xs font-mono px-1.5 py-0.5 rounded border ${SEV_STYLE[issue.severity] || ""}`}
                      >
                        {issue.severity}
                      </span>
                      <span className="text-xs font-mono text-gray-600">
                        {issue.category}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mb-2 leading-relaxed">
                      {issue.description}
                    </p>
                    {issue.file_path && (
                      <div className="text-xs font-mono text-cyan-600 bg-black/30 border border-gray-800 rounded px-2 py-1 inline-block mb-2">
                        {issue.file_path}
                        {issue.line_start ? `:${issue.line_start}` : ""}
                      </div>
                    )}
                    {issue.suggestion && (
                      <div className="bg-black/30 border border-gray-800 rounded p-3 text-xs font-mono text-gray-300 leading-relaxed">
                        <span className="text-emerald-400">💡 </span>
                        {issue.suggestion}
                      </div>
                    )}
                    {issue.code_snippet && (
                      <pre className="mt-2 bg-black/40 border border-gray-800 rounded p-3 text-xs font-mono text-gray-400 overflow-x-auto">
                        <code>{issue.code_snippet}</code>
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {review?.status === "completed" && allIssues.length === 0 && (
        <div className="text-center py-16 bg-[#111827] border border-emerald-400/20 rounded-lg">
          <div className="text-5xl mb-3">✅</div>
          <div className="text-emerald-400 font-mono font-semibold text-lg">
            No issues found
          </div>
          <div className="text-gray-600 text-sm mt-1">
            All three agents gave this PR a clean bill of health.
          </div>
        </div>
      )}

      {review?.error && (
        <div className="bg-red-900/20 border border-red-400/30 rounded-lg p-4 mt-4">
          <div className="text-xs font-mono text-red-400 uppercase tracking-wider mb-1">
            Error
          </div>
          <pre className="text-sm font-mono text-red-400/80">
            {review.error}
          </pre>
        </div>
      )}
    </div>
  );
}
