export type ConfidenceLevel = "high" | "medium" | "low" | "unknown";

const HIGH_CONFIDENCE = 0.9;
const MEDIUM_CONFIDENCE = 0.75;

export const DOCUMENT_TYPE_LABELS: Record<string, string> = { rg: "RG", cnh: "CNH", cpf: "CPF" };

export const STATUS_LABELS: Record<string, string> = {
  pending_review: "Pendente de revisão",
  reviewed: "Revisado",
};

export function confidenceLevel(confidence: number | null | undefined): ConfidenceLevel {
  if (confidence === null || confidence === undefined) return "unknown";
  if (confidence >= HIGH_CONFIDENCE) return "high";
  return confidence >= MEDIUM_CONFIDENCE ? "medium" : "low";
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatCpf(cpf: string | null): string {
  if (!cpf || cpf.length !== 11) return cpf ?? "";
  return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9)}`;
}

export function initials(name: string | null): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function plural(count: number, singular: string, pluralForm: string): string {
  return `${count.toLocaleString("pt-BR")} ${count === 1 ? singular : pluralForm}`;
}
