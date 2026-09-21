import React from "react";
import { LucideIcon, Inbox } from "lucide-react";
import { motion } from "framer-motion";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState = React.memo(function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex flex-col items-center justify-center py-20 px-6 text-center"
    >
      <div className="relative mb-6">
        <div className="h-20 w-20 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center glow-blue-sm">
          <Icon className="h-9 w-9 text-primary/80" />
        </div>
        {/* Outer glow ring */}
        <div className="absolute inset-0 rounded-2xl bg-primary/5 blur-xl" />
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      {description && (
        <p className="text-sm text-slate-400 mt-2 max-w-xs leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </motion.div>
  );
});

interface ErrorStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

export const ErrorState = React.memo(function ErrorState({
  title = "Something went wrong",
  description = "An error occurred while loading data. Please try again.",
  action,
}: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <div className="h-16 w-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4">
        <span className="text-red-400 text-2xl">✕</span>
      </div>
      <h3 className="text-base font-semibold text-red-300">{title}</h3>
      <p className="text-sm text-slate-500 mt-1 max-w-xs">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </motion.div>
  );
});
