const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

async function request(
  method: string,
  path: string,
  token: string,
  body?: unknown
) {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get: (path: string, token: string) => request("GET", path, token),
  post: (path: string, body: unknown, token: string) =>
    request("POST", path, token, body),
  put: (path: string, body: unknown, token: string) =>
    request("PUT", path, token, body),
  patch: (path: string, token: string, body?: unknown) =>
    request("PATCH", path, token, body),
  del: (path: string, token: string) => request("DELETE", path, token),
};
