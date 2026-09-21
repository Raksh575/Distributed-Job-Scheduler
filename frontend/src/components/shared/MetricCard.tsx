import React from "react";
import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { GlassCard } from "./GlassCard";
import { cn } from "../../utils/cn";

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  trend?: number; // percentage change
  suffix?: string;
  loading?: boolean;
  className?: string;
  onClick?: () => void;
}

export const MetricCard = React.memo(function MetricCard({
  label,
  value,
  icon: Icon,
  iconColor = "text-blue-400",
  iconBg = "bg-blue-500/10",
  trend,
  suffix,
  loading = false,
  className,
  onClick,
}: MetricCardProps) {
  if (loading) {
    return (
      <GlassCard className={className}>
        <div className="flex items-center justify-between">
          <div className="space-y-3 flex-1">
            <div className="skeleton h-3 w-20 rounded" />
            <div className="skeleton h-8 w-16 rounded" />
            <div className="skeleton h-3 w-14 rounded" />
          </div>
          <div className="skeleton h-12 w-12 rounded-xl shrink-0" />
        </div>
      </GlassCard>
    );
  }

  const trendPositive = trend !== undefined && trend > 0;
  const trendNegative = trend !== undefined && trend < 0;
  const TrendIcon = trendPositive ? TrendingUp : trendNegative ? TrendingDown : Minus;

  return (
    <GlassCard
      interactive={!!onClick}
      className={cn("group", className)}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest truncate">
            {label}
          </p>
          <p className="text-3xl font-bold text-white mt-2 font-mono tracking-tight">
            {value}
            {suffix && (
              <span className="text-base font-normal text-slate-400 ml-1">{suffix}</span>
            )}
          </p>
          {trend !== undefined && (
            <div
              className={cn(
                "flex items-center gap-1 mt-2 text-xs font-medium",
                trendPositive ? "text-emerald-400" : trendNegative ? "text-red-400" : "text-slate-500"
              )}
            >
              <TrendIcon className="h-3 w-3" />
              <span>{Math.abs(trend).toFixed(1)}% vs last hour</span>
            </div>
          )}
        </div>
        <div
          className={cn(
            "h-12 w-12 rounded-xl flex items-center justify-center shrink-0 ml-4 transition-all duration-300",
            iconBg,
            "group-hover:scale-110"
          )}
        >
          <Icon className={cn("h-6 w-6", iconColor)} />
        </div>
      </div>
    </GlassCard>
  );
});
