import React, { useEffect, useState } from "react";
import { motion, useAnimation } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { cn } from "../../utils/cn";

interface AnimatedKPICardProps {
  label: string;
  value: string | number;
  suffix?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  trend?: { value: number; isPositive: boolean };
}

export const AnimatedKPICard = React.memo(({
  label, value, suffix = "", icon: Icon, iconColor = "text-blue-400", iconBg = "bg-blue-500/10", trend
}: AnimatedKPICardProps) => {
  const [prevValue, setPrevValue] = useState(value);
  const controls = useAnimation();

  useEffect(() => {
    if (value !== prevValue) {
      controls.start({
        scale: [1, 1.1, 1],
        color: ["#ffffff", "#60a5fa", "#ffffff"],
        transition: { duration: 0.3 }
      });
      setPrevValue(value);
    }
  }, [value, prevValue, controls]);

  return (
    <div className="relative overflow-hidden bg-white/[0.02] border border-white/10 rounded-2xl p-5 hover:bg-white/[0.04] transition-colors shadow-2xl backdrop-blur-md">
      <div className="absolute top-0 right-0 p-32 bg-gradient-to-bl from-white/[0.03] to-transparent rounded-full -mr-20 -mt-20 pointer-events-none" />
      
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">{label}</span>
        <div className={cn("p-2 rounded-xl border border-white/5", iconBg)}>
          <Icon className={cn("w-4 h-4", iconColor)} />
        </div>
      </div>
      
      <div className="flex items-baseline gap-2">
        <motion.span animate={controls} className="text-3xl font-bold text-white font-mono tracking-tight">
          {value}
        </motion.span>
        {suffix && <span className="text-sm font-medium text-slate-500">{suffix}</span>}
      </div>
      
      {trend && (
        <div className="mt-3 flex items-center gap-1.5 text-xs">
          <span className={cn(
            "font-semibold",
            trend.isPositive ? "text-emerald-400" : "text-rose-400"
          )}>
            {trend.isPositive ? "+" : "-"}{trend.value}%
          </span>
          <span className="text-slate-500">vs last hour</span>
        </div>
      )}
    </div>
  );
});

AnimatedKPICard.displayName = "AnimatedKPICard";
