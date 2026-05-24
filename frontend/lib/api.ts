const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function startReview(repo: string, prNumber: number, token?: string) {
  const res = await fetch(`${API_URL}/api/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_full_name: repo, pr_number: prNumber, github_token: token }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getReview(reviewId: string) {
  const res = await fetch(`${API_URL}/api/reviews/${reviewId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listReviews() {
  const res = await fetch(`${API_URL}/api/reviews`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAnalyticsSummary() {
  const res = await fetch(`${API_URL}/api/analytics/summary`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAnalyticsTrend(days = 14) {
  const res = await fetch(`${API_URL}/api/analytics/trend?days=${days}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getTopFiles() {
  const res = await fetch(`${API_URL}/api/analytics/top-files`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function createSSEConnection(reviewId: string, onEvent: (type: string, data: any) => void): () => void {
  const url = `${API_URL}/api/stream/${reviewId}`;
  const es = new EventSource(url);

  es.onmessage = (e) => {
    try {
      const payload = JSON.parse(e.data);
      onEvent(payload.type, payload.data);
    } catch {}
  };

  es.onerror = () => es.close();

  return () => es.close();
}
