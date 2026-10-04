import { Lightbulb, ScanLine, ShieldCheck, Sparkles, Sun, Upload } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { Dropzone } from "../components/Dropzone";
import { PageHeader } from "../components/Navbar";

export function UploadPage() {
  const navigate = useNavigate();
  const [front, setFront] = useState<File | null>(null);
  const [back, setBack] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!front && !back) {
      setError("Envie pelo menos uma foto do documento.");
      return;
    }
    const form = new FormData();
    if (front) form.append("front", front);
    if (back) form.append("back", back);
    setBusy(true);
    setError(null);
    try {
      const document = await api.upload(form);
      navigate(`/documentos/${document.id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Falha ao enviar.");
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Enviar documento"
        icon={Upload}
        subtitle="RG, CNH ou CPF. O tipo é identificado automaticamente."
      />
      <form className="card" onSubmit={submit}>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="upload-grid">
          <Dropzone label="Frente" hint="Toque para tirar uma foto ou escolher um arquivo" file={front} onChange={setFront} />
          <Dropzone label="Verso" hint="Toque para tirar uma foto ou escolher um arquivo" file={back} onChange={setBack} />
        </div>
        <ul className="tips">
          <li>
            <ScanLine size={18} />
            Enquadre o documento inteiro, sem cortar as bordas.
          </li>
          <li>
            <Sun size={18} />
            Evite reflexo e sombra sobre o documento.
          </li>
          <li>
            <Sparkles size={18} />
            Em pé ou deitado: a orientação é corrigida sozinha.
          </li>
        </ul>
        <button className="button button-block button-lg" type="submit" disabled={busy || (!front && !back)}>
          <ScanLine size={20} />
          Extrair dados
        </button>
        <p className="privacy-note">
          <ShieldCheck size={16} />
          As fotos originais são guardadas criptografadas neste servidor.
        </p>
      </form>

      {busy && (
        <div className="overlay">
          <div className="overlay-box">
            <div className="spinner" />
            <strong>Lendo o documento…</strong>
            <span>
              <Lightbulb size={14} /> Corrigindo orientação, extraindo campos e validando o CPF.
            </span>
          </div>
        </div>
      )}
    </>
  );
}
