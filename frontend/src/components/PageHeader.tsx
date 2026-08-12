import type { ReactNode } from "react";

export default function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: ReactNode;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3 text-center">
      <span className="eyebrow eyebrow-accent">{eyebrow}</span>
      <h1 className="type-display text-3xl sm:text-4xl">{title}</h1>
      {description && <p className="max-w-md text-sm text-muted">{description}</p>}
    </div>
  );
}
