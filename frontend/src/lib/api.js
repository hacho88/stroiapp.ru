const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

const TOKEN_KEY = "ai_manager_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { ...extra, "X-Auth-Token": token } : extra;
}

function handleResponse(response) {
  if (response.status === 401) {
    clearToken();
    window.dispatchEvent(new Event("ai-auth-expired"));
    throw new Error("Требуется авторизация");
  }
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function apiLogin(login, password) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login, password }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `API error: ${response.status}`);
  if (data.token) setToken(data.token);
  return data;
}

export async function apiGet(path) {
  const response = await fetch(`${API_URL}${path}`, { headers: authHeaders() });
  return handleResponse(response);
}

export async function apiUpload(path, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  return handleResponse(response);
}

export function apiUrl(path) {
  return `${API_URL}${path}`;
}

export async function apiPost(path, body) {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

export async function apiDelete(path) {
  const response = await fetch(`${API_URL}${path}`, { method: "DELETE", headers: authHeaders() });
  return handleResponse(response);
}
