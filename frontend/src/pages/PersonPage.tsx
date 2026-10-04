import { ArrowLeft, CircleAlert, FilePlus2, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { PageHead } from "../components/AppShell";
import { DeleteDialog } from "../components/DeleteDialog";
import { EmptyState } from "../components/ListState";
import { Confidence, StatusLabel } from "../components/Status";
import { useToast } from "../components/Toast";
import { DOCUMENT_TYPE_LABELS, formatCpf, formatDate, formatDateTime } from "../format";
import type { PersonDetail } from "../types";

export function PersonPage() {
  const personId = Number(useParams().id);
  const navigate = useNavigate();
  const toast = useToast();
  const [person, setPerson] = useState<PersonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    api.person(personId).then(setPerson).catch((caught) => setError(caught.message));
  }, [personId]);

  if (error) {
    return (
      <div className="page">
        <EmptyState icon={CircleAlert} title={error} text="O cadastro pode ter sido apagado." action={<Link to="/pessoas" className="button button-secondary">Ver pessoas</Link>} />
      </div>
    );
  }
  if (!person) return <div className="spinner spinner-page" />;

  const remove = async () => {
    await api.deletePerson(person.id);
    toast(`${person.full_name ?? "Pessoa"} apagada.`);
    navigate("/pessoas");
  };

  const details: [string, string | null][] = [
    ["CPF", formatCpf(person.cpf)],
    ["Nascimento", person.birth_date],
    ["Naturalidade", person.birthplace],
    ["Mãe", person.mother_name],
    ["Pai", person.father_name],
    ["Cadastro", formatDate(person.created_at)],
  ];

  return (
    <div className="page">
      <PageHead
        back={
          <Link to="/pessoas" className="breadcrumb">
            <ArrowLeft size={14} />
            Pessoas
          </Link>
        }
        title={person.full_name || "Sem nome"}
        description={<StatusLabel status={person.status} />}
        actions={
          <div className="actions-row">
            <Link to="/novo" className="button button-secondary">
              <FilePlus2 size={16} strokeWidth={1.75} />
              Adicionar documento
            </Link>
            <button className="button button-danger-ghost" type="button" onClick={() => setDeleting(true)}>
              <Trash2 size={16} strokeWidth={1.75} />
              Apagar pessoa
            </button>
          </div>
        }
      />
      <div className="review">
        <section className="panel">
          <div className="panel-head">
            <h2>Dados consolidados</h2>
          </div>
          <dl className="meta-list panel-body">
            {details.map(([label, value]) => (
              <div key={label} className="contents">
                <dt>{label}</dt>
                <dd>{value || "—"}</dd>
              </div>
            ))}
          </dl>
        </section>
        <section className="panel list-panel">
          <div className="panel-head">
            <h2>Documentos ({person.documents})</h2>
          </div>
          <table className="table">
            <tbody>
              {person.document_list.map((document) => (
                <tr key={document.id} onClick={() => navigate(`/documentos/${document.id}`)}>
                  <td className="cell-primary">
                    <Link to={`/documentos/${document.id}`} className="cell-name" onClick={(event) => event.stopPropagation()}>
                      {document.thumbnail_url ? <img className="thumb" src={document.thumbnail_url} alt="" /> : <span className="thumb" />}
                      <span>{DOCUMENT_TYPE_LABELS[document.doc_type] ?? document.doc_type.toUpperCase()}</span>
                    </Link>
                  </td>
                  <td className="cell-meta w-100"><Confidence value={document.confidence} /></td>
                  <td className="cell-meta w-190"><StatusLabel status={document.status} /></td>
                  <td className="cell-meta col-optional w-150">{formatDateTime(document.processed_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
      <DeleteDialog
        open={deleting}
        title="Apagar pessoa e documentos"
        description={
          <>
            <strong>{person.full_name ?? "Esta pessoa"}</strong> será removida do cadastro junto com tudo o que está vinculado a ela.
          </>
        }
        documents={person.documents}
        images={person.images}
        confirmationValues={[person.full_name ?? "", person.cpf ?? ""]}
        confirmationLabel="Para confirmar, digite o nome completo ou o CPF"
        onConfirm={remove}
        onClose={() => setDeleting(false)}
      />
    </div>
  );
}
