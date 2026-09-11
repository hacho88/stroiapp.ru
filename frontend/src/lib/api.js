const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export async function apiGet(path) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function apiUpload(path, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export function apiUrl(path) {
  return `${API_URL}${path}`;
}

export async function apiPost(path, body) {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function apiDelete(path) {
  const response = await fetch(`${API_URL}${path}`, { method: "DELETE" });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}
