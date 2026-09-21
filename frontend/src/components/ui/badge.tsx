import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../utils/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border transition-colors focus:outline-none focus:ring-1 focus:ring-primary",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary/10 text-primary-light border-primary/20",
        secondary:
          "border-transparent bg-slate-900 text-slate-300 border-card-border",
        destructive:
          "border-transparent bg-red-500/10 text-red-400 border-red-500/20",
        success:
          "border-transparent bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        warning:
          "border-transparent bg-amber-500/10 text-amber-400 border-amber-500/20",
        outline: "text-slate-300 border-card-border bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
