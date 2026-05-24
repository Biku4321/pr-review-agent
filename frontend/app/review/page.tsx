"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { startReview } from "../../lib/api";

const DEMO_PRS = [
  { repo: "demo-org/vulnerable-app", pr: 1, label: "SQL Injection + XSS demo" },
  { repo: "demo-org/slow-queries-app", pr: 3, label: "N+1 query + missing index" },
  { repo: "demo-org/messy-code", pr: 7, label: "Code quality issues" },
];

export default function ReviewPage() {
  const router = useRouter();
  const [repo, setRepo] = useState("");
  const [prNum, setPrNum] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (r = repo, p = prNum) => {
    if (!r || !p) return;
    setLoading(true);
    setError("");
    try {
      const review = await startReview(r, parseInt(p), token || undefined);
      router.push(`/review/${review.review_id}`);
    } catch (e: any) {
      setError(e.message || "Failed to start review");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">New Review</h1>
        <p className="text-muted text-sm mt-1 font-mono">Paste a GitHub PR to start AI analysis</p>
      </div>

      {/* Main form */}
      <div className="bg-surface border border-border rounded-lg p-6 mb-6">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-muted uppercase tracking-wider mb-1.5">
              Repository
            </label>
            <input
              type="text"
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              placeholder="owner/repo-name"
              className="w-full bg-bg border border-border rounded px-3 py-2.5 text-sm font-mono text-gray-100 placeholder-muted focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-muted uppercase tracking-wider mb-1.5">
              Pull Request Number
            </label>
            <input
              type="number"
              value={prNum}
              onChange={(e) => setPrNum(e.target.value)}
              placeholder="42"
              className="w-full bg-bg border border-border rounded px-3 py-2.5 text-sm font-mono text-gray-100 placeholder-muted focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-muted uppercase tracking-wider mb-1.5">
              GitHub Token <span className="text-muted normal-case">(optional, for private repos)</span>
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="ghp_..."
              className="w-full bg-bg border border-border rounded px-3 py-2.5 text-sm font-mono text-gray-100 placeholder-muted focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          {error && (
            <div className="bg-danger/10 border border-danger/30 rounded px-3 py-2 text-danger text-sm font-mono">
              {error}
            </div>
          )}

          <button
            onClick={() => submit()}
            disabled={loading || !repo || !prNum}
            className="w-full py-3 bg-accent text-bg font-semibold font-mono text-sm rounded hover:bg-cyan-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-bg border-t-transparent rounded-full animate-spin" />
                Starting review...
              </>
            ) : (
              "▶ Run AI Review"
            )}
          </button>
        </div>
      </div>

      {/* Demo PRs */}
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <span className="text-xs font-mono text-muted uppercase tracking-wider">Demo PRs</span>
        </div>
        <div className="divide-y divide-border">
          {DEMO_PRS.map((d) => (
            <button
              key={d.label}
              onClick={() => {
                setRepo(d.repo);
                setPrNum(String(d.pr));
                submit(d.repo, String(d.pr));
              }}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 transition-colors text-left group"
            >
              <span className="w-2 h-2 rounded-full bg-danger shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-mono text-gray-200">{d.label}</div>
                <div className="text-xs text-muted">
                  {d.repo} <span className="text-accent">#{d.pr}</span>
                </div>
              </div>
              <span className="text-muted group-hover:text-accent transition-colors text-sm">→</span>
            </button>
          ))}
        </div>
      </div>

      {/* Architecture callout */}
      <div className="mt-6 bg-accent/5 border border-accent/20 rounded-lg p-4">
        <div className="text-xs font-mono text-accent uppercase tracking-wider mb-2">Multi-agent architecture</div>
        <div className="flex gap-3 flex-wrap">
          {["🔒 Security", "⚡ Performance", "🧹 Quality"].map((a) => (
            <span key={a} className="text-xs font-mono text-muted bg-surface border border-border rounded px-2 py-1">
              {a}
            </span>
          ))}
          <span className="text-xs font-mono text-muted">run in parallel via LangGraph</span>
        </div>
      </div>
    </div>
  );
}
