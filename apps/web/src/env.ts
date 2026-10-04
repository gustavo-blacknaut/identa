import { z } from "zod";

const schema = z.object({
  IDENTA_API_URL: z
    .url({ message: "IDENTA_API_URL precisa ser uma URL completa, por exemplo http://127.0.0.1:8000" })
    .default("http://127.0.0.1:8000")
    .transform((value) => value.replace(/\/+$/, "")),
});

export type ServerEnv = z.infer<typeof schema>;

export function readServerEnv(source: Record<string, string | undefined> = process.env): ServerEnv {
  const parsed = schema.safeParse({ IDENTA_API_URL: source.IDENTA_API_URL || undefined });
  if (!parsed.success) {
    const lines = parsed.error.issues.map((issue) => `  - ${issue.path.join(".")}: ${issue.message}`);
    throw new Error(`Configuração inválida do identa-web:\n${lines.join("\n")}`);
  }
  return parsed.data;
}
