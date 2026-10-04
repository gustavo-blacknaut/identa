import { LayoutDashboard, LogOut, Plus, Users, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth";

const LINKS = [
  { to: "/", label: "Painel", icon: LayoutDashboard, end: true },
  { to: "/pessoas", label: "Pessoas", icon: Users, end: false },
];

export function Logo({ size = 34 }: { size?: number }) {
  return <img className="logo" src="/logo.png" alt="" width={size} height={size} />;
}

export function Navbar() {
  const { user, logout } = useAuth();
  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to="/" className="brand">
            <Logo />
            <span className="brand-name">
              Green <strong>OCR</strong>
            </span>
          </NavLink>
          <nav className="nav-links" aria-label="Principal">
            {LINKS.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} className="nav-link">
                <Icon size={18} />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="nav-actions">
            <NavLink to="/enviar" className="button nav-cta">
              <Plus size={18} />
              Enviar documento
            </NavLink>
            <div className="user-chip" title={user?.username}>
              <span className="user-avatar">{user?.username.slice(0, 1).toUpperCase()}</span>
              <span className="user-name">{user?.username}</span>
            </div>
            <button className="icon-button" type="button" onClick={logout} aria-label="Sair" title="Sair">
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </header>
      <nav className="bottom-nav" aria-label="Navegação">
        <NavLink to="/" end className="bottom-link">
          <LayoutDashboard size={22} />
          <span>Painel</span>
        </NavLink>
        <NavLink to="/enviar" className="bottom-link bottom-cta">
          <span className="bottom-cta-circle">
            <Plus size={26} />
          </span>
          <span>Enviar</span>
        </NavLink>
        <NavLink to="/pessoas" className="bottom-link">
          <Users size={22} />
          <span>Pessoas</span>
        </NavLink>
      </nav>
    </>
  );
}

type PageHeaderProps = {
  title: string;
  icon: LucideIcon;
  subtitle?: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({ title, icon: Icon, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-title">
        <span className="page-icon">
          <Icon size={22} />
        </span>
        <div>
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}
