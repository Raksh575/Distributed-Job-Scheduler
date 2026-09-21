import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNotification } from "../../store/useNotification";
import { CheckCircle, AlertCircle, AlertTriangle, Info, X } from "lucide-react";
import { cn } from "../../utils/cn";

const toastIcons = {
  success: { icon: CheckCircle, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  error:   { icon: AlertCircle, color: "text-red-400",     bg: "bg-red-500/10 border-red-500/20" },
  warning: { icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  info:    { icon: Info,         color: "text-blue-400",   bg: "bg-blue-500/10 border-blue-500/20" },
};

export const ToastContainer = React.memo(function ToastContainer() {
  const { toasts, removeToast } = useNotification();

  return (
    <div className="fixed bottom-6 right-6 z-[200] flex flex-col gap-3 pointer-events-none max-w-sm w-full">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => {
          const cfg = toastIcons[toast.type];
          const Icon = cfg.icon;

          return (
            <motion.div
              key={toast.id}
              layout
              initial={{ opacity: 0, x: 60, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 60, scale: 0.9 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className={cn(
                "pointer-events-auto flex items-start gap-3 rounded-xl border p-4",
                "backdrop-blur-xl shadow-2xl",
                "bg-[rgba(8,14,28,0.92)]",
                cfg.bg
              )}
            >
              <Icon className={cn("h-5 w-5 shrink-0 mt-0.5", cfg.color)} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white">{toast.title}</p>
                {toast.message && (
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{toast.message}</p>
                )}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-slate-500 hover:text-slate-300 transition-colors shrink-0"
              >
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
});
