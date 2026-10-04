import { Camera, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

type DropzoneProps = {
  label: string;
  hint: string;
  file: File | null;
  onChange: (file: File | null) => void;
};

export function Dropzone({ label, hint, file, onChange }: DropzoneProps) {
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  return (
    <label className={`dropzone${preview ? " has-image" : ""}`}>
      <input type="file" accept="image/*" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
      <span className="dropzone-tag badge">{label}</span>
      {preview ? (
        <>
          <img src={preview} alt={`Prévia: ${label}`} />
          <span className="dropzone-change button button-secondary">
            <RefreshCw size={16} />
            Trocar foto
          </span>
        </>
      ) : (
        <>
          <span className="dropzone-icon">
            <Camera size={26} />
          </span>
          <span className="dropzone-title">{label}</span>
          <span className="dropzone-hint">{hint}</span>
        </>
      )}
    </label>
  );
}
