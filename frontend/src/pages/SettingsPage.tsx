import { Monitor, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { PageHead } from "../components/AppShell";
import { useTheme, type ThemePreference } from "../theme";
import type { SystemInfo } from "../types";

const THEMES: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Claro", icon: Sun },
  { value: "dark", label: "Escuro", icon: Moon },
  { value: "system", label: "Sistema", icon: Monitor },
];

export function SettingsPage() {
  const { user } = useAuth();
  const { preference, setPreference } = useTheme();
  const [system, setSystem] = useState<SystemInfo | null>(null);

  useEffect(() => {
    api.system().then(setSystem).catch(() => undefined);
  }, []);

  return (
    <div className="page">
      <PageHead title="Configurações" description="Preferências de exibição e informações do servidor." />
      <div className="settings">
        <section className="panel">
          <div className="panel-head">
            <h2>Aparência</h2>
          </div>
          <div className="panel-body stack">
            <div className="segmented" role="group" aria-label="Tema">
              {THEMES.map(({ value, label, icon: Icon }) => (
                <button key={value} type="button" aria-pressed={preference === value} onClick={() => setPreference(value)}>
                  <Icon size={14} strokeWidth={1.75} />
                  {label}
                </button>
              ))}
            </div>
            <p className="muted flush">A preferência fica salva neste navegador.</p>
          </div>
        </section>
        <section className="panel">
          <div className="panel-head">
            <h2>Conta</h2>
          </div>
          <dl className="meta-list panel-body">
            <dt>Usuário</dt>
            <dd>{user?.username}</dd>
            <dt>Sessão</dt>
            <dd>Expira após 8 horas</dd>
            <dt>Senha</dt>
            <dd className="mono">python -m app.cli create-user {user?.username}</dd>
          </dl>
        </section>
        <section className="panel">
          <div className="panel-head">
            <h2>Servidor</h2>
          </div>
          <dl className="meta-list panel-body">
            <dt>Motor de OCR</dt>
            <dd>{system ? (system.ocr_engine === "paddle" ? "PaddleOCR (local)" : system.ocr_engine) : "—"}</dd>
            <dt>Armazenamento</dt>
            <dd>{system?.encrypted_storage ? "Imagens criptografadas com AES-256-GCM" : "—"}</dd>
            <dt>Limite de envio</dt>
            <dd>{system ? `${system.max_upload_mb} MB por imagem` : "—"}</dd>
          </dl>
        </section>
      </div>
    </div>
  );
}
