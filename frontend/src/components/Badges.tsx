import { CheckCircle2, Clock } from "lucide-react";
import { confidenceLevel, formatPercent } from "../format";
import type { DocumentStatus } from "../types";

export function StatusBadge({ status }: { status: DocumentStatus }) {
  if (status === "reviewed") {
    return (
      <span className="badge badge-high">
        <CheckCircle2 size={14} />
        Revisado
      </span>
    );
  }
  return (
    <span className="badge badge-medium">
      <Clock size={14} />
      Pendente
    </span>
  );
}

export function ConfidenceBadge({ value }: { value: number | null }) {
  if (value === null) return <span className="badge badge-unknown">não encontrado</span>;
  return <span className={`badge badge-${confidenceLevel(value)}`}>{formatPercent(value)}</span>;
}
