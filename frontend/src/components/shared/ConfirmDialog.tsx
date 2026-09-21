import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, X } from "lucide-react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning" | "info";
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog = React.memo(function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  isLoading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCancel}
            className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm"
          />
          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 20 }}
            transition={{ type: "spring", stiffness: 350, damping: 28 }}
            className="fixed inset-0 z-[101] flex items-center justify-center p-4"
          >
            <div className="glass-card gradient-border rounded-2xl p-6 w-full max-w-md shadow-2xl">
              <div className="flex items-start gap-4">
                <div
                  className={`h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ${
                    variant === "danger"
                      ? "bg-red-500/10 text-red-400"
                      : variant === "warning"
                      ? "bg-amber-500/10 text-amber-400"
                      : "bg-blue-500/10 text-blue-400"
                  }`}
                >
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-semibold text-white">{title}</h3>
                  <p className="text-sm text-slate-400 mt-1 leading-relaxed">{description}</p>
                </div>
                <button
                  onClick={onCancel}
                  className="text-slate-500 hover:text-slate-300 transition-colors shrink-0"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="flex gap-3 mt-6 justify-end">
                <button
                  onClick={onCancel}
                  className="btn-ghost px-4 py-2 rounded-lg text-sm font-medium text-slate-300"
                >
                  {cancelLabel}
                </button>
                <button
                  onClick={onConfirm}
                  disabled={isLoading}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                    variant === "danger"
                      ? "btn-danger"
                      : "btn-primary text-white"
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isLoading ? "Processing..." : confirmLabel}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
});
