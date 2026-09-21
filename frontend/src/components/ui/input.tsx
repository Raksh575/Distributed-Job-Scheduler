import * as React from "react";
import { cn } from "../../utils/cn";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "w-full bg-slate-950/40 border border-slate-800 text-slate-100 rounded-lg px-4 py-2.5 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all duration-200 placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50 text-sm",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
