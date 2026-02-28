const API_BASE = process.env.NEXT_PUBLIC_DM_API_BASE || "http://127.0.0.1:9134";

function buildApiUrl(path: string): string {
  const base = API_BASE.replace(/\/+$/, "");
  let p = path.startsWith("/") ? path : `/${path}`;
  if (base.endsWith("/api") && p.startsWith("/api/")) {
    p = p.slice(4);
  }
  return `${base}${p}`;
}

function getTokenFromBrowser(): string | null {
  if (typeof window === "undefined") return null;
  const fromStorage = localStorage.getItem("dmm_access_token");
  if (fromStorage) return fromStorage;
  const cookie = document.cookie
    .split(";")
    .map((v) => v.trim())
    .find((v) => v.startsWith("dmm_access_token="));
  return cookie ? decodeURIComponent(cookie.substring("dmm_access_token=".length)) : null;
}

function authHeaders(base?: HeadersInit): HeadersInit {
  const merged: Record<string, string> = { ...((base as Record<string, string>) || {}) };
  const token = getTokenFromBrowser();
  if (token) {
    merged.Authorization = `Bearer ${token}`;
  }
  return merged;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(buildApiUrl(path), { cache: "no-store", headers: authHeaders() });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return res.json();
}

export async function apiPost<T>(path: string): Promise<T> {
  const res = await fetch(buildApiUrl(path), { method: "POST", headers: authHeaders() });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload?.detail || `POST ${path} failed: ${res.status}`);
  }
  return res.json();
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(buildApiUrl(path), {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload?.detail || `POST ${path} failed: ${res.status}`);
  }
  return res.json();
}

export async function apiPatchJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(buildApiUrl(path), {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload?.detail || `PATCH ${path} failed: ${res.status}`);
  }
  return res.json();
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(buildApiUrl(path), {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload?.detail || `DELETE ${path} failed: ${res.status}`);
  }
  return res.json();
}

export async function apiPutJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(buildApiUrl(path), {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload?.detail || `PUT ${path} failed: ${res.status}`);
  }
  return res.json();
}

export { API_BASE, buildApiUrl, getTokenFromBrowser };
