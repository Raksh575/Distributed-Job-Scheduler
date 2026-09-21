import React from "react";
import { cn } from "../../utils/cn";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  interactive?: boolean;
  glow?: boolean;
  gradient?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
  onClick?: () => void;
}

const paddingMap = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export const GlassCard = React.memo(function GlassCard({
  children,
  className,
  interactive = false,
  glow = false,
  gradient = false,
  padding = "md",
  onClick,
}: GlassCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "glass-card rounded-2xl",
        paddingMap[padding],
        interactive && "glass-card-interactive",
        glow && "glow-blue-sm",
        gradient && "gradient-border",
        className
      )}
    >
      {children}
    </div>
  );
});
