import { titleCase } from "../lib/format";

export function StatusBadge({ value }: { value?: string | null }) {
  const normalized = (value ?? "unknown").toLowerCase().replaceAll("_", "-");
  return <span className={`status status--${normalized}`}>{titleCase(value)}</span>;
}
