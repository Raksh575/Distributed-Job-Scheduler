import React from "react";
import { cn } from "../../utils/cn";

export type StatusType =
  | "queued"
  | "running"
  | "success"
  | "failed"
  | "cancelled"
  | "scheduled"
  | "claimed"
  | "active"
  | "idle"
  | "offline"
  | "paused";

const statusConfig: Record<
  StatusType,
  { label: string; dot: string; bg: string; text: string }
> = {
  queued:    { label: "Queued",    dot: "bg-amber-400",   bg: "bg-amber-500/10",   text: "text-amber-300" },
  running:   { label: "Running",   dot: "bg-blue-400",    bg: "bg-blue-500/10",    text: "text-blue-300" },
  success:   { label: "Success",   dot: "bg-emerald-400", bg: "bg-emerald-500/10", text: "text-emerald-300" },
  failed:    { label: "Failed",    dot: "bg-red-400",     bg: "bg-red-500/10",     text: "text-red-300" },
  cancelled: { label: "Cancelled", dot: "bg-slate-500",   bg: "bg-slate-500/10",   text: "text-slate-400" },
  scheduled: { label: "Scheduled", dot: "bg-purple-400",  bg: "bg-purple-500/10",  text: "text-purple-300" },
  claimed:   { label: "Claimed",   dot: "bg-cyan-400",    bg: "bg-cyan-500/10",    text: "text-cyan-300" },
  active:    { label: "Active",    dot: "bg-emerald-400", bg: "bg-emerald-500/10", text: "text-emerald-300" },
  idle:      { label: "Idle",      dot: "bg-slate-400",   bg: "bg-slate-500/10",   text: "text-slate-300" },
  offline:   { label: "Offline",   dot: "bg-red-500",     bg: "bg-red-500/10",     text: "text-red-400" },
  paused:    { label: "Paused",    dot: "bg-yellow-500",  bg: "bg-yellow-500/10",  text: "text-yellow-300" },
};

interface StatusBadgeProps {
  status: StatusType;
  pulse?: boolean;
  size?: "sm" | "md";
  className?: string;
}

export const StatusBadge = React.memo(function StatusBadge({
  status,
  pulse = false,
  size = "md",
  className,
}: StatusBadgeProps) {
  const cfg = statusConfig[status] ?? statusConfig.cancelled;
  const isAnimated = pulse && (status === "running" || status === "active");

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-semibold border border-transparent",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        cfg.bg,
        cfg.text,
        className
      )}
    >
      <span
        className={cn(
          "rounded-full shrink-0",
          size === "sm" ? "h-1.5 w-1.5" : "h-2 w-2",
          cfg.dot,
          isAnimated && "animate-pulse"
        )}
      />
      {cfg.label}
    </span>
  );
});
