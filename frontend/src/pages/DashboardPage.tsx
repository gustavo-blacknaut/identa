import { CheckCircle2, Clock, FileText, LayoutDashboard, Plus, Search, Users } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { ConfidenceBadge, StatusBadge } from "../components/Badges";
import { PageHeader } from "../components/Navbar";
import { formatCpf, relativeTime } from "../format";
import type { DocumentStatus } from "../types";
import { usePolling } from "../usePolling";

const REFRESH_INTERVAL_MS = 4000;
const FILTERS: { value: DocumentStatus | "all"; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "pending_review", label: "Pendentes" },
  { value: "reviewed", label: "Revisados" },
];

export function DashboardPage() {
  const { data, error, updatedAt } = usePolling(api.overview, REFRESH_INTERVAL_MS);
  const [filter, setFilter] = useState<DocumentStatus | "all">("all");
  const [query, setQuery] = useState("");

  const documents = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const digits = normalized.replace(/\D/g, "");
    return (data?.documents ?? []).filter((document) => {
      if (filter !== "all" && document.status !== filter) return false;
      if (!normalized) return true;
      const nameMatch = (document.full_name ?? "").toLowerCase().includes(normalized);
      const cpfMatch = digits.length > 0 && (document.cpf ?? "").includes(digits);
      return nameMatch || cpfMatch;
    });
  }, [data, filter, query]);

  const stats = data?.stats;

  return (
    <>
      <PageHeader
        title="Painel"
        icon={LayoutDashboard}
        subtitle={
          <span className="live">
            <span className={`live-dot${error ? " offline" : ""}`} />
            {error ? "Sem conexão com o servidor" : updatedAt ? "Atualizando automaticamente" : "Carregando…"}
          </span>
        }
        actions={
          <Link to="/enviar" className="button hide-mobile">
            <Plus size={18} />
            Enviar documento
          </Link>
        }
      />

      <section className="stats">
        <StatCard icon={FileText} label="Documentos" value={stats?.documents} tone="accent" />
        <StatCard icon={Clock} label="Aguardando revisão" value={stats?.pending} tone="medium" />
        <StatCard icon={Users} label="Pessoas" value={stats?.people} tone="info" />
      </section>

      <section className="card card-flush">
        <div className="toolbar">
          <div className="segmented" role="tablist">
            {FILTERS.map((option) => (
              <button
                key={option.value}
                type="button"
                role="tab"
                aria-selected={filter === option.value}
                className={filter === option.value ? "active" : ""}
                onClick={() => setFilter(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
          <label className="search">
            <Search size={16} />
            <input
              type="search"
              placeholder="Buscar por nome ou CPF"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
        </div>

        {data === null && !error ? (
          <div className="skeleton-list">
            {[0, 1, 2].map((item) => (
              <div key={item} className="skeleton-row" />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <EmptyDocuments hasAny={(data?.documents.length ?? 0) > 0} />
        ) : (
          <ul className="doc-list">
            {documents.map((document) => (
              <li key={document.id}>
                <Link to={`/documentos/${document.id}`} className="doc-row">
                  <span className="doc-thumb">
                    {document.thumbnail_url ? (
                      <img src={document.thumbnail_url} alt="" loading="lazy" />
                    ) : (
                      <FileText size={20} />
                    )}
                  </span>
                  <span className="doc-main">
                    <span className="doc-name">{document.full_name || "Nome não identificado"}</span>
                    <span className="doc-meta">
                      <span className="badge badge-type">{document.doc_type.toUpperCase()}</span>
                      {document.cpf && <span className="mono">{formatCpf(document.cpf)}</span>}
                      <span>{relativeTime(document.processed_at)}</span>
                    </span>
                  </span>
                  <span className="doc-side">
                    <ConfidenceBadge value={document.confidence} />
                    <StatusBadge status={document.status} />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

type StatCardProps = {
  icon: typeof FileText;
  label: string;
  value: number | undefined;
  tone: "accent" | "medium" | "info";
};

function StatCard({ icon: Icon, label, value, tone }: StatCardProps) {
  return (
    <div className="stat">
      <span className={`stat-icon stat-${tone}`}>
        <Icon size={20} />
      </span>
      <span>
        <span className="stat-value">{value ?? "–"}</span>
        <span className="stat-label">{label}</span>
      </span>
    </div>
  );
}

function EmptyDocuments({ hasAny }: { hasAny: boolean }) {
  if (hasAny) {
    return (
      <div className="empty">
        <span className="empty-icon">
          <Search size={24} />
        </span>
        <strong>Nada encontrado</strong>
        Nenhum documento corresponde ao filtro.
      </div>
    );
  }
  return (
    <div className="empty">
      <span className="empty-icon">
        <CheckCircle2 size={24} />
      </span>
      <strong>Nenhum documento ainda</strong>
      Envie a frente e o verso de um documento para começar.
      <Link to="/enviar" className="button">
        <Plus size={18} />
        Enviar documento
      </Link>
    </div>
  );
}
