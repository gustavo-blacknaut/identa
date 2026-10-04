import { Lock, LogIn } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useAuth } from "../auth";
import { Logo } from "../components/Navbar";

export function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Não foi possível entrar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="login-screen">
      <div className="login-glow" aria-hidden="true" />
      <form className="login-card" onSubmit={submit}>
        <div className="login-brand">
          <Logo size={56} />
          <h1>
            Green <strong>OCR</strong>
          </h1>
          <p>Leitura de documentos com revisão segura</p>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <label className="field">
          <span className="field-label">Usuário</span>
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            autoFocus
            required
          />
        </label>
        <label className="field">
          <span className="field-label">Senha</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <button className="button button-block button-lg" type="submit" disabled={busy}>
          <LogIn size={18} />
          {busy ? "Entrando…" : "Entrar"}
        </button>
        <p className="login-footnote">
          <Lock size={14} />
          Dados armazenados localmente e criptografados
        </p>
      </form>
    </main>
  );
}
