import type { DocumentDetail, DocumentType, Overview, Person, User } from "./types";

export const UNAUTHORIZED_EVENT = "green-ocr:unauthorized";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("X-Requested-With", "green-ocr");
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...init, headers, credentials: "same-origin" });
  if (response.status === 401 && !path.startsWith("/api/auth/")) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = typeof payload?.detail === "string" ? payload.detail : "Algo deu errado. Tente novamente.";
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  me: () => request<User>("/api/auth/me"),
  login: (username: string, password: string) =>
    request<User>("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  overview: () => request<Overview>("/api/overview"),
  documentTypes: () => request<DocumentType[]>("/api/document-types"),
  document: (id: number) => request<DocumentDetail>(`/api/documents/${id}`),
  upload: (form: FormData) => request<DocumentDetail>("/api/documents", { method: "POST", body: form }),
  saveDocument: (id: number, values: Record<string, string>) =>
    request<DocumentDetail>(`/api/documents/${id}`, { method: "PUT", body: JSON.stringify({ values }) }),
  reprocess: (id: number, docType: string | null) =>
    request<DocumentDetail>(`/api/documents/${id}/reprocess`, {
      method: "POST",
      body: JSON.stringify({ doc_type: docType }),
    }),
  deleteDocument: (id: number) => request<void>(`/api/documents/${id}`, { method: "DELETE" }),
  people: () => request<Person[]>("/api/people"),
  deletePerson: (id: number) => request<void>(`/api/people/${id}`, { method: "DELETE" }),
};
