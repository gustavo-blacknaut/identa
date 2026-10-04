import {
  AlertTriangle,
  ArrowLeft,
  ArrowUpDown,
  ChevronDown,
  FileSearch,
  Fingerprint,
  IdCard,
  PenLine,
  RefreshCw,
  Save,
  Sparkles,
  Trash2,
  User,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { ConfidenceBadge, StatusBadge } from "../components/Badges";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { PageHeader } from "../components/Navbar";
import { useToast } from "../components/Toast";
import { confidenceLevel, relativeTime } from "../format";
import type { DocumentDetail, DocumentType, Field, FieldSection, ImageInfo } from "../types";

const SIDE_LABELS: Record<string, string> = { front: "Frente", back: "Verso", open: "Frente" };
const CROP_LABELS: Record<string, string> = { portrait: "Foto", signature: "Assinatura", fingerprint: "Polegar" };
const CROP_ICONS: Record<string, typeof User> = { portrait: User, signature: PenLine, fingerprint: Fingerprint };
const SECTIONS: { key: FieldSection; title: string; icon: typeof User }[] = [
  { key: "personal", title: "Dados pessoais", icon: User },
  { key: "document", title: "Documento", icon: IdCard },
];
const WIDE_FIELDS = new Set(["full_name", "mother_name", "father_name", "mrz_raw", "civil_registry"]);

export function DocumentPage() {
  const { id } = useParams();
  const documentId = Number(id);
  const navigate = useNavigate();
  const toast = useToast();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [types, setTypes] = useState<DocumentType[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);
  const [reprocessType, setReprocessType] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [viewer, setViewer] = useState<ImageInfo | null>(null);

  const load = useCallback((detail: DocumentDetail) => {
    setDocument(detail);
    setValues(Object.fromEntries(detail.fields.map((field) => [field.name, field.value])));
  }, []);

  useEffect(() => {
    api.document(documentId).then(load).catch((caught) => setError(caught.message));
    api.documentTypes().then(setTypes).catch(() => undefined);
  }, [documentId, load]);

  const dirty = useMemo(
    () => document?.fields.some((field) => (values[field.name] ?? "") !== field.value) ?? false,
    [document, values],
  );

  if (error) {
    return (
      <div className="card empty">
        <span className="empty-icon">
          <AlertTriangle size={24} />
        </span>
        <strong>{error}</strong>
        <Link to="/" className="button button-secondary">
          Voltar ao painel
        </Link>
      </div>
    );
  }

  if (!document) {
    return <div className="spinner page-spinner" />;
  }

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      load(await api.saveDocument(document.id, values));
      toast("Dados salvos com sucesso.");
    } catch (caught) {
      toast(caught instanceof Error ? caught.message : "Falha ao salvar.", "error");
    } finally {
      setSaving(false);
    }
  };

  const reprocess = async () => {
    setReprocessing(true);
    try {
      load(await api.reprocess(document.id, reprocessType || null));
      toast("Documento reprocessado.");
    } catch (caught) {
      toast(caught instanceof Error ? caught.message : "Falha ao reprocessar.", "error");
    } finally {
      setReprocessing(false);
    }
  };

  const remove = async () => {
    try {
      await api.deleteDocument(document.id);
      toast("Documento apagado.");
      navigate("/");
    } catch (caught) {
      toast(caught instanceof Error ? caught.message : "Falha ao apagar.", "error");
      setConfirmDelete(false);
    }
  };

  const setValue = (name: string, value: string) => setValues((current) => ({ ...current, [name]: value }));
  const swapParents = () =>
    setValues((current) => ({ ...current, mother_name: current.father_name ?? "", father_name: current.mother_name ?? "" }));

  const extraFields = document.fields.filter((field) => field.section === "extra");
  const extraFound = extraFields.filter((field) => field.value).length;
  const hasParents = document.fields.some((field) => field.name === "mother_name");

  return (
    <>
      <Link to="/" className="back-link">
        <ArrowLeft size={16} />
        Voltar ao painel
      </Link>
      <PageHeader
        title={document.full_name || "Nome não identificado"}
        icon={IdCard}
        subtitle={
          <span className="header-badges">
            <span className="badge badge-type">{document.type_name}</span>
            {document.type_detected && (
              <span className="badge badge-accent">
                <Sparkles size={13} />
                Identificado automaticamente
              </span>
            )}
            <StatusBadge status={document.status} />
            {document.reviewed_manually && <span className="badge badge-unknown">corrigido manualmente</span>}
            <span className="muted">Processado {relativeTime(document.processed_at)}</span>
          </span>
        }
      />

      {document.notes.includes("cpf_corrected") && (
        <div className="alert alert-warn">
          <AlertTriangle size={18} />O CPF lido não passava no dígito verificador e foi relido e corrigido
          automaticamente. Confira antes de salvar.
        </div>
      )}
      {document.notes.includes("cpf_unverified") && (
        <div className="alert alert-error">
          <AlertTriangle size={18} />O CPF lido não passa no dígito verificador e não foi possível corrigir
          automaticamente.
        </div>
      )}

      <div className="review">
        <aside className="gallery">
          <div className="card">
            <h2 className="card-title">Imagens</h2>
            <div className="pages">
              {document.pages.map((image) => (
                <button key={image.id} type="button" className="page-image" onClick={() => setViewer(image)}>
                  <img src={image.thumbnail_url} alt={SIDE_LABELS[image.side] ?? image.side} />
                  <span className="page-label">{SIDE_LABELS[image.side] ?? image.side}</span>
                </button>
              ))}
            </div>
            {document.crops.length > 0 && (
              <>
                <h3 className="subtitle">Recortes</h3>
                <div className="crops">
                  {document.crops.map((image) => {
                    const Icon = CROP_ICONS[image.kind] ?? User;
                    return (
                      <button key={image.id} type="button" className="crop" onClick={() => setViewer(image)}>
                        <img src={image.thumbnail_url} alt={CROP_LABELS[image.kind]} />
                        <span>
                          <Icon size={13} />
                          {CROP_LABELS[image.kind] ?? image.kind}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </aside>

        <form className="card fields-card" onSubmit={save}>
          <div className="legend">
            <span className="legend-title">Confiança</span>
            <span className="badge badge-high">alta</span>
            <span className="badge badge-medium">média</span>
            <span className="badge badge-low">baixa</span>
            <span className="badge badge-unknown">não encontrado</span>
          </div>

          {SECTIONS.map(({ key, title, icon: Icon }) => (
            <section key={key} className="section">
              <h2 className="section-title">
                <Icon size={16} />
                {title}
              </h2>
              <div className="fields-grid">
                {document.fields
                  .filter((field) => field.section === key)
                  .map((field) => (
                    <FieldInput key={field.name} field={field} value={values[field.name] ?? ""} onChange={setValue} />
                  ))}
              </div>
              {key === "personal" && hasParents && (
                <button type="button" className="link swap" onClick={swapParents}>
                  <ArrowUpDown size={14} />
                  Trocar pai e mãe
                </button>
              )}
            </section>
          ))}

          {extraFields.length > 0 && (
            <details className="section extras" open={extraFound > 0}>
              <summary className="section-title">
                <span>
                  <FileSearch size={16} />
                  Outras informações {extraFound > 0 && <span className="count">{extraFound}</span>}
                </span>
                <ChevronDown size={18} className="chevron" />
              </summary>
              <div className="fields-grid">
                {extraFields.map((field) => (
                  <FieldInput key={field.name} field={field} value={values[field.name] ?? ""} onChange={setValue} />
                ))}
              </div>
            </details>
          )}

          <div className="action-bar">
            {dirty && <span className="unsaved">Alterações não salvas</span>}
            <button className="button" type="submit" disabled={saving}>
              <Save size={18} />
              {saving ? "Salvando…" : "Confirmar e salvar"}
            </button>
          </div>
        </form>
      </div>

      <section className="card tools-card">
        <div className="tools">
          <div className="tool">
            <label className="field">
              <span className="field-label">Reprocessar como</span>
              <select value={reprocessType} onChange={(event) => setReprocessType(event.target.value)}>
                <option value="">Identificar automaticamente</option>
                {types.map((type) => (
                  <option key={type.doc_type} value={type.doc_type}>
                    {type.display_name}
                  </option>
                ))}
              </select>
            </label>
            <button className="button button-secondary" type="button" onClick={reprocess} disabled={reprocessing}>
              <RefreshCw size={18} className={reprocessing ? "spin" : ""} />
              {reprocessing ? "Reprocessando…" : "Reprocessar OCR"}
            </button>
          </div>
          <button className="button button-danger" type="button" onClick={() => setConfirmDelete(true)}>
            <Trash2 size={18} />
            Apagar documento
          </button>
        </div>
        <details className="raw">
          <summary>Texto reconhecido pelo OCR</summary>
          <pre>{document.raw_text}</pre>
        </details>
      </section>

      <ConfirmDialog
        open={confirmDelete}
        title="Apagar documento?"
        message={
          <>
            O documento <strong>{document.full_name || `#${document.id}`}</strong>, as fotos originais e os recortes serão
            apagados definitivamente. Essa ação não pode ser desfeita.
          </>
        }
        confirmLabel="Apagar definitivamente"
        onConfirm={remove}
        onClose={() => setConfirmDelete(false)}
      />

      {viewer && (
        <div className="lightbox" onClick={() => setViewer(null)}>
          <button className="icon-button lightbox-close" type="button" aria-label="Fechar">
            <X size={22} />
          </button>
          <img src={viewer.full_url} alt="" onClick={(event) => event.stopPropagation()} />
        </div>
      )}
    </>
  );
}

type FieldInputProps = {
  field: Field;
  value: string;
  onChange: (name: string, value: string) => void;
};

function FieldInput({ field, value, onChange }: FieldInputProps) {
  const level = value && field.value === value ? confidenceLevel(field.confidence) : value ? "edited" : "unknown";
  const wide = WIDE_FIELDS.has(field.name) || field.kind === "multiline";
  return (
    <label className={`field field-${level}${field.issues.length ? " field-invalid" : ""}${wide ? " field-wide" : ""}`}>
      <span className="field-label">
        {field.label}
        {field.value && field.value === value ? (
          <ConfidenceBadge value={field.confidence} />
        ) : value ? (
          <span className="badge badge-unknown">editado</span>
        ) : null}
      </span>
      {field.kind === "multiline" ? (
        <textarea rows={3} className="mono" value={value} onChange={(event) => onChange(field.name, event.target.value)} />
      ) : (
        <input
          value={value}
          onChange={(event) => onChange(field.name, event.target.value)}
          inputMode={field.kind === "date" || field.kind === "cpf" ? "numeric" : undefined}
          placeholder={field.kind === "date" ? "dd/mm/aaaa" : field.kind === "cpf" ? "000.000.000-00" : undefined}
          className={field.kind === "cpf" ? "mono" : undefined}
        />
      )}
      {field.issues.map((issue) => (
        <em key={issue} className="issue">
          {issue}
        </em>
      ))}
    </label>
  );
}
