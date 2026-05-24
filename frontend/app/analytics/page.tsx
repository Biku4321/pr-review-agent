"use client";
import { useEffect, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { getAnalyticsSummary, getAnalyticsTrend, getTopFiles } from "../../lib/api";

const SEVERITY_COLORS = { critical: "#f87171", high: "#fb923c", medium: "#fbbf24", low: "#60a5fa" };
const CAT_COLORS = ["#22d3ee", "#818cf8", "#34d399", "#f472b6"];

function StatCard({ label, value, sub, accent }: any) {
  return (
    <div className="bg-[#111827] border border-gray-800 rounded-lg p-5">
      <div className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-3xl font-mono font-bold ${accent ? "text-red-400" : "text-gray-100"}`}>{value}</div>
      {sub && <div className="text-xs text-gray-600 mt-1 font-mono">{sub}</div>}
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0a0e17] border border-gray-800 rounded-lg px-3 py-2 text-xs font-mono shadow-xl">
      <div className="text-gray-400 mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} style={{ color: p.color }}>{p.name}: {p.value}</div>
      ))}
    </div>
  );
};

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [trend, setTrend] = useState<any[]>([]);
  const [topFiles, setTopFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getAnalyticsSummary(), getAnalyticsTrend(14), getTopFiles()])
      .then(([s, t, f]) => { setSummary(s); setTrend(t); setTopFiles(f); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="text-center py-20 text-gray-600 font-mono text-sm">
      <div className="inline-block w-6 h-6 border-2 border-gray-800 border-t-cyan-400 rounded-full animate-spin mb-3" />
      <div>Loading analytics...</div>
    </div>
  );

  const catData = summary ? Object.entries(summary.category_breakdown).map(([k, v]) => ({
    name: k.charAt(0).toUpperCase() + k.slice(1), value: v as number
  })) : [];

  const sevData = summary ? Object.entries(summary.severity_breakdown).map(([k, v]) => ({
    name: k.charAt(0).toUpperCase() + k.slice(1), value: v as number,
    fill: SEVERITY_COLORS[k as keyof typeof SEVERITY_COLORS] || "#888"
  })) : [];

  return (
    <div className="animate-[fadeIn_0.4s_ease-out]">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
          <p className="text-gray-600 text-sm mt-1 font-mono">Trends and patterns across all reviews</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <StatCard label="Total Reviews" value={summary?.total_reviews ?? 0} />
        <StatCard label="Completed" value={summary?.completed_reviews ?? 0} />
        <StatCard label="Issues Found" value={summary?.total_issues_found ?? 0} />
        <StatCard label="Avg / PR" value={summary?.avg_issues_per_pr ?? 0} sub="issues per review" />
        <StatCard label="Critical %" value={`${summary?.critical_percentage ?? 0}%`} accent sub="of all issues" />
      </div>

      {/* Trend chart */}
      <div className="bg-[#111827] border border-gray-800 rounded-lg p-5 mb-4">
        <div className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-4">Issue trend — last 14 days</div>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={trend} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <defs>
              {Object.entries(SEVERITY_COLORS).map(([k, c]) => (
                <linearGradient key={k} id={`grad_${k}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={c} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={c} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fill: "#4b5563", fontSize: 11, fontFamily: "monospace" }} />
            <YAxis tick={{ fill: "#4b5563", fontSize: 11, fontFamily: "monospace" }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, fontFamily: "monospace", color: "#6b7280" }} />
            <Area type="monotone" dataKey="critical" name="Critical" stroke="#f87171" fill="url(#grad_critical)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="high" name="High" stroke="#fb923c" fill="url(#grad_high)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="medium" name="Medium" stroke="#fbbf24" fill="url(#grad_medium)" strokeWidth={1.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {/* Category pie */}
        <div className="bg-[#111827] border border-gray-800 rounded-lg p-5">
          <div className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-4">Issues by category</div>
          <div className="flex items-center justify-center gap-6">
            <ResponsiveContainer width={160} height={160}>
              <PieChart>
                <Pie data={catData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={4} dataKey="value">
                  {catData.map((_: any, i: number) => (
                    <Cell key={i} fill={CAT_COLORS[i % CAT_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2">
              {catData.map((d: any, i: number) => (
                <div key={d.name} className="flex items-center gap-2 text-sm font-mono">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: CAT_COLORS[i % CAT_COLORS.length] }} />
                  <span className="text-gray-400">{d.name}</span>
                  <span className="text-gray-200 font-semibold ml-auto pl-4">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Severity bar */}
        <div className="bg-[#111827] border border-gray-800 rounded-lg p-5">
          <div className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-4">Issues by severity</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={sevData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#4b5563", fontSize: 11, fontFamily: "monospace" }} />
              <YAxis tick={{ fill: "#4b5563", fontSize: 11, fontFamily: "monospace" }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" name="Issues" radius={[3, 3, 0, 0]}>
                {sevData.map((entry: any, i: number) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top files */}
      {topFiles.length > 0 && (
        <div className="bg-[#111827] border border-gray-800 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <span className="text-xs font-mono text-gray-600 uppercase tracking-wider">Top files by issue count</span>
          </div>
          <div className="divide-y divide-gray-900">
            {topFiles.map((f: any, i: number) => (
              <div key={i} className="flex items-center gap-4 px-4 py-3">
                <span className="text-gray-700 font-mono text-sm w-5 shrink-0">{i + 1}</span>
                <span className="font-mono text-sm text-cyan-500 flex-1 truncate">{f.file}</span>
                <div className="flex items-center gap-3 shrink-0">
                  {f.critical > 0 && (
                    <span className="text-xs font-mono text-red-400">{f.critical} critical</span>
                  )}
                  <div className="w-24 bg-gray-900 rounded-full h-1.5">
                    <div className="h-full bg-cyan-500 rounded-full" style={{
                      width: `${Math.min(100, (f.total / (topFiles[0]?.total || 1)) * 100)}%`
                    }} />
                  </div>
                  <span className="text-xs font-mono text-gray-400 w-12 text-right">{f.total} issues</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
