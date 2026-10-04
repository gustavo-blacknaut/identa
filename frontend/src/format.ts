export type ConfidenceLevel = "high" | "medium" | "low" | "unknown";

const HIGH_CONFIDENCE = 0.9;
const MEDIUM_CONFIDENCE = 0.75;
const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

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

export function relativeTime(iso: string, now: number = Date.now()): string {
  const elapsed = now - new Date(iso).getTime();
  if (elapsed < MINUTE) return "agora mesmo";
  if (elapsed < HOUR) return `há ${Math.floor(elapsed / MINUTE)} min`;
  if (elapsed < DAY) return `há ${Math.floor(elapsed / HOUR)} h`;
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
}
