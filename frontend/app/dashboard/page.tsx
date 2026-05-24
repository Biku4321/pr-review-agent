"use client";
import { useEffect, useState } from "react";
import { listReviews } from "../../lib/api";
import Link from "next/link";

const sev = (n: number, cls: string) =>
  n > 0 ? <span className={`font-mono text-xs px-2 py-0.5 rounded ${cls}`}>{n}</span> : null;

const STATUS_STYLE: Record<string, string> = {
  completed: "text-success border-success/30 bg-success/10",
  running: "text-accent border-accent/30 bg-accent/10 scan-badge",
  pending: "text-warning border-warning/30 bg-warning/10",
  failed: "text-danger border-danger/30 bg-danger/10",
};

export default function DashboardPage() {
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await listReviews();
      setReviews(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  const totalIssues = reviews.reduce((a, r) => a + (r.total_issues || 0), 0);
  const totalCritical = reviews.reduce((a, r) => a + (r.critical_count || 0), 0);
  const completed = reviews.filter((r) => r.status === "completed").length;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Review Dashboard</h1>
          <p className="text-muted text-sm mt-1 font-mono">Multi-agent AI code analysis</p>
        </div>
        <Link
          href="/review"
          className="px-4 py-2 bg-accent text-bg font-semibold text-sm rounded font-mono hover:bg-cyan-300 transition-colors"
        >
          + New Review
        </Link>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total Reviews", value: reviews.length, accent: false },
          { label: "Completed", value: completed, accent: false },
          { label: "Issues Found", value: totalIssues, accent: false },
          { label: "Critical", value: totalCritical, accent: true },
        ].map((m) => (
          <div key={m.label} className="bg-surface border border-border rounded-lg p-4">
            <div className="text-muted text-xs font-mono uppercase tracking-wider mb-1">{m.label}</div>
            <div className={`text-3xl font-mono font-semibold ${m.accent ? "text-danger" : "text-gray-100"}`}>
              {m.value}
            </div>
          </div>
        ))}
      </div>

      {/* Reviews Table */}
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center gap-2">
          <span className="text-xs font-mono text-muted uppercase tracking-wider">Recent Reviews</span>
          {reviews.some((r) => r.status === "running") && (
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse-fast" />
          )}
        </div>

        {loading ? (
          <div className="p-8 text-center text-muted font-mono text-sm">Loading...</div>
        ) : reviews.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-muted font-mono text-sm">No reviews yet.</p>
            <Link href="/review" className="text-accent text-sm font-mono hover:underline">
              Start your first review →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {reviews.map((r) => (
              <Link
                key={r.review_id}
                href={`/review/${r.review_id}`}
                className="flex items-center gap-4 px-4 py-3 hover:bg-white/5 transition-colors group"
              >
                {/* Status */}
                <span className={`text-xs font-mono px-2 py-0.5 rounded border ${STATUS_STYLE[r.status] || ""}`}>
                  {r.status}
                </span>

                {/* Repo + PR */}
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-sm text-gray-200 truncate">
                    <span className="text-muted">{r.repo}</span>
                    <span className="text-accent mx-1">#{r.pr_number}</span>
                  </div>
                  {r.pr_title && (
                    <div className="text-xs text-muted truncate mt-0.5">{r.pr_title}</div>
                  )}
                </div>

                {/* Severity badges */}
                <div className="flex items-center gap-1.5 shrink-0">
                  {sev(r.critical_count, "bg-danger/20 text-danger border border-danger/30")}
                  {sev(r.total_issues - r.critical_count, "bg-warning/20 text-warning border border-warning/30")}
                  {r.total_issues === 0 && r.status === "completed" && (
                    <span className="text-xs font-mono text-success">✓ clean</span>
                  )}
                </div>

                {/* Date */}
                <div className="text-xs text-muted font-mono shrink-0">
                  {new Date(r.created_at).toLocaleDateString()}
                </div>

                <span className="text-muted group-hover:text-accent transition-colors">→</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
