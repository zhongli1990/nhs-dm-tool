const API_BASE = process.env.NEXT_PUBLIC_DM_API_BASE || "http://localhost:8099";

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return res.json();
}

export async function apiPost<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST" });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload?.detail || `POST ${path} failed: ${res.status}`);
  }
  return res.json();
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload?.detail || `POST ${path} failed: ${res.status}`);
  }
  return res.json();
}

export { API_BASE };
