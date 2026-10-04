import { AlertTriangle } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmLabel: string;
  onConfirm: () => Promise<void> | void;
  onClose: () => void;
};

export function ConfirmDialog({ open, title, message, confirmLabel, onConfirm, onClose }: ConfirmDialogProps) {
  const [busy, setBusy] = useState(false);
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    cancelRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  if (!open) return null;

  const confirm = async () => {
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={() => !busy && onClose()}>
      <div
        className="modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        onClick={(event) => event.stopPropagation()}
      >
        <span className="modal-icon">
          <AlertTriangle size={24} />
        </span>
        <h2 id="confirm-title">{title}</h2>
        <div className="modal-message">{message}</div>
        <div className="modal-actions">
          <button ref={cancelRef} className="button button-secondary" type="button" onClick={onClose} disabled={busy}>
            Cancelar
          </button>
          <button className="button button-danger-solid" type="button" onClick={confirm} disabled={busy}>
            {busy ? "Apagando…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
