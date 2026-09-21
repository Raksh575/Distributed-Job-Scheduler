import React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "../../utils/cn";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  actions?: React.ReactNode;
  className?: string;
}

export const PageHeader = React.memo(function PageHeader({
  title,
  subtitle,
  icon: Icon,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4", className)}>
      <div className="flex items-center gap-3 min-w-0">
        {Icon && (
          <div className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0 glow-blue-sm">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        )}
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-white tracking-tight truncate">{title}</h1>
          {subtitle && (
            <p className="text-sm text-slate-400 mt-0.5 truncate">{subtitle}</p>
          )}
        </div>
      </div>
      {actions && (
        <div className="flex items-center gap-2 shrink-0">{actions}</div>
      )}
    </div>
  );
});
