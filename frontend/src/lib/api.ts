// Strip any trailing slashes so paths like "/api/todos" never become "//api/todos".
// Also strips any accidental path suffix (e.g. "/api" at the end of the host URL)
// that would cause double prefixes like "/api/api/todos".
const BACKEND_URL = (process.env.BACKEND_URL || "http://localhost:8000").replace(
  /\/+$/,
  ""
);

async function request(
  method: string,
  path: string,
  token: string,
  body?: unknown
) {
  const url = `${BACKEND_URL}${path}`;
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  let res: Response;
  try {
    res = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    // Network-level failure (ECONNREFUSED, DNS, etc.) — log the URL so it
    // appears in Vercel function logs and is easy to spot.
    console.error(`[api] ${method} ${url} — network error:`, err);
    throw new Error(`Backend unreachable (${url}): ${(err as Error).message}`);
  }
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    console.error(`[api] ${method} ${url} → ${res.status}`, error);
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
