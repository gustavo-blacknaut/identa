import { ScrollText, SearchX } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { PageHead } from "../components/AppShell";
import { EmptyState, ListBar, SkeletonRows } from "../components/ListState";
import { formatDateTime } from "../format";
import { useInfiniteList, useSentinel } from "../useInfiniteList";

const ACTION_LABELS: Record<string, string> = {
  login: "Login",
  create: "Processamento",
  review: "Revisão",
  reprocess: "Reprocessamento",
  delete: "Exclusão",
};
const ENTITY_LABELS: Record<string, string> = { document: "Documento", person: "Pessoa", user: "Usuário" };
const FILTER_KEYS = ["action", "from", "to"];

export function AuditPage() {
  const [params, setParams] = useSearchParams();
  const filters = new URLSearchParams();
  for (const key of FILTER_KEYS) {
    const value = params.get(key);
    if (value) filters.set(key, value);
  }
  const list = useInfiniteList(api.audit, filters);
  const sentinel = useSentinel(list.loadMore, list.hasMore);
  const active = filters.toString() !== "";

  const update = (key: string, value: string) =>
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value) next.set(key, value);
        else next.delete(key);
        return next;
      },
      { replace: true },
    );

  return (
    <div className="page page-fill">
      <PageHead title="Auditoria" description="Registro de acessos e alterações. Não contém dados pessoais dos documentos." />
      <section className="panel list-panel">
        <div className="filters filters-compact expanded">
          <label>
            <span className="visually-hidden">Ação</span>
            <select value={params.get("action") ?? ""} onChange={(event) => update("action", event.target.value)}>
              <option value="">Todas as ações</option>
              {Object.entries(ACTION_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <div className="range" role="group" aria-label="Período">
            <input type="date" value={params.get("from") ?? ""} onChange={(event) => update("from", event.target.value)} aria-label="Período: início" />
            <span>até</span>
            <input type="date" value={params.get("to") ?? ""} onChange={(event) => update("to", event.target.value)} aria-label="Período: fim" />
          </div>
        </div>
        <ListBar total={list.total} singular="registro" pluralLabel="registros" filtered={active} onClear={() => setParams(new URLSearchParams(), { replace: true })} />
        <div className="list-scroll">
          {list.total === null && !list.error ? (
            <SkeletonRows />
          ) : list.items.length === 0 ? (
            <EmptyState icon={active ? SearchX : ScrollText} title="Nenhum registro" text={active ? "Nenhuma ação no período ou filtro escolhido." : "As ações aparecem aqui conforme o sistema é usado."} />
          ) : (
            <table className="table table-static">
              <thead>
                <tr>
                  <th className="w-150">Data e hora</th>
                  <th className="w-150">Usuário</th>
                  <th className="w-150">Ação</th>
                  <th>Registro</th>
                </tr>
              </thead>
              <tbody>
                {list.items.map((entry) => (
                  <tr key={entry.id}>
                    <td className="cell-primary mono">{formatDateTime(entry.occurred_at)}</td>
                    <td className="cell-meta">{entry.username ?? "—"}</td>
                    <td className="cell-meta">{ACTION_LABELS[entry.action] ?? entry.action}</td>
                    <td className="cell-meta">
                      {ENTITY_LABELS[entry.entity] ?? entry.entity}
                      {entry.entity_id !== null && <span className="mono muted"> #{entry.entity_id}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div ref={sentinel} className="list-sentinel" />
          {list.loading && list.items.length > 0 && <div className="list-loading">Carregando mais…</div>}
        </div>
      </section>
    </div>
  );
}
