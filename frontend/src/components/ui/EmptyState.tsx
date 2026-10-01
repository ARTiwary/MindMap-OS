import type { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-20 px-6">
      {icon && <div className="mb-4 text-accent/70">{icon}</div>}
      <h3 className="font-display text-xl mb-2">{title}</h3>
      {description && <p className="text-white/50 max-w-sm mb-6 text-sm">{description}</p>}
      {action}
    </div>
  );
}
