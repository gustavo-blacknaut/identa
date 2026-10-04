export type User = {
  id: number;
  username: string;
};

export type DocumentType = {
  doc_type: string;
  display_name: string;
};

export type DocumentStatus = "pending_review" | "reviewed";

export type DocumentSummary = {
  id: number;
  doc_type: string;
  type_name: string;
  full_name: string | null;
  cpf: string | null;
  status: DocumentStatus;
  confidence: number | null;
  processed_at: string;
  thumbnail_url: string | null;
};

export type ImageInfo = {
  id: number;
  side: string;
  kind: string;
  thumbnail_url: string;
  full_url: string;
  original_url: string;
};

export type FieldSection = "personal" | "document" | "extra";

export type Field = {
  name: string;
  label: string;
  kind: string;
  section: FieldSection;
  value: string;
  confidence: number | null;
  issues: string[];
};

export type DocumentDetail = DocumentSummary & {
  reviewed_manually: boolean;
  type_detected: boolean;
  notes: string[];
  fields: Field[];
  pages: ImageInfo[];
  crops: ImageInfo[];
  raw_text: string;
  person_id: number | null;
};

export type Stats = {
  documents: number;
  pending: number;
  people: number;
};

export type Overview = {
  stats: Stats;
  documents: DocumentSummary[];
};

export type Person = {
  id: number;
  full_name: string | null;
  cpf: string | null;
  birth_date: string | null;
  documents: number;
  updated_at: string;
};
