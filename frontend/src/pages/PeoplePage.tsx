import { Trash2, Users } from "lucide-react";
import { useState } from "react";
import { api } from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { PageHeader } from "../components/Navbar";
import { useToast } from "../components/Toast";
import { formatCpf, initials, relativeTime } from "../format";
import type { Person } from "../types";
import { usePolling } from "../usePolling";

const REFRESH_INTERVAL_MS = 6000;

export function PeoplePage() {
  const { data, refresh } = usePolling(api.people, REFRESH_INTERVAL_MS);
  const [pending, setPending] = useState<Person | null>(null);
  const toast = useToast();

  const remove = async () => {
    if (!pending) return;
    try {
      await api.deletePerson(pending.id);
      toast("Pessoa e documentos apagados.");
      await refresh();
    } catch (caught) {
      toast(caught instanceof Error ? caught.message : "Falha ao apagar.", "error");
    } finally {
      setPending(null);
    }
  };

  return (
    <>
      <PageHeader
        title="Pessoas"
        icon={Users}
        subtitle="Cadastro consolidado a partir dos documentos revisados, sem duplicar CPF."
      />
      <section className="card card-flush">
        {data === null ? (
          <div className="skeleton-list">
            {[0, 1, 2].map((item) => (
              <div key={item} className="skeleton-row" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <div className="empty">
            <span className="empty-icon">
              <Users size={24} />
            </span>
            <strong>Nenhuma pessoa cadastrada</strong>
            As pessoas aparecem aqui quando um documento é revisado e salvo.
          </div>
        ) : (
          <ul className="doc-list">
            {data.map((person) => (
              <li key={person.id} className="doc-row">
                <span className="avatar">{initials(person.full_name)}</span>
                <span className="doc-main">
                  <span className="doc-name">{person.full_name || "Sem nome"}</span>
                  <span className="doc-meta">
                    {person.cpf && <span className="mono">{formatCpf(person.cpf)}</span>}
                    {person.birth_date && <span>Nasc. {person.birth_date}</span>}
                    <span>
                      {person.documents} {person.documents === 1 ? "documento" : "documentos"}
                    </span>
                    <span>Atualizado {relativeTime(person.updated_at)}</span>
                  </span>
                </span>
                <span className="doc-side">
                  <button className="button button-danger" type="button" onClick={() => setPending(person)}>
                    <Trash2 size={16} />
                    <span className="hide-mobile">Apagar</span>
                  </button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <ConfirmDialog
        open={pending !== null}
        title="Apagar pessoa?"
        message={
          <>
            <strong>{pending?.full_name || "Esta pessoa"}</strong> e todos os documentos e imagens vinculados serão apagados
            definitivamente. Essa ação não pode ser desfeita.
          </>
        }
        confirmLabel="Apagar definitivamente"
        onConfirm={remove}
        onClose={() => setPending(null)}
      />
    </>
  );
}
