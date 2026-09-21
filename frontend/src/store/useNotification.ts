import { create } from "zustand";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface NotificationState {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

export const useNotification = create<NotificationState>((set) => ({
  toasts: [],

  addToast: (toast) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const newToast: Toast = { id, duration: 4000, ...toast };
    set((state) => ({ toasts: [...state.toasts, newToast] }));

    // Auto-dismiss
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, newToast.duration);
  },

  removeToast: (id) => {
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
  },

  clearAll: () => set({ toasts: [] }),
}));

// Convenience helpers
export const toast = {
  success: (title: string, message?: string) =>
    useNotification.getState().addToast({ type: "success", title, message }),
  error: (title: string, message?: string) =>
    useNotification.getState().addToast({ type: "error", title, message, duration: 6000 }),
  warning: (title: string, message?: string) =>
    useNotification.getState().addToast({ type: "warning", title, message }),
  info: (title: string, message?: string) =>
    useNotification.getState().addToast({ type: "info", title, message }),
};
