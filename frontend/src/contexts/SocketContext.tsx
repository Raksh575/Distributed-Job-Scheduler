import React, { createContext, useContext, useEffect, useState, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../store/useAuth";

interface SocketContextType {
  connected: boolean;
  subscribe: (topic: string) => void;
  unsubscribe: (topic: string) => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export function useSocket() {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error("useSocket must be used within a SocketProvider");
  }
  return context;
}

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const { token } = useAuth();
  const queryClient = useQueryClient();

  const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

  useEffect(() => {
    if (!token) {
      if (socketRef.current) {
        socketRef.current.close();
      }
      return;
    }

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      console.log("WebSocket connected.");
      // Subscribe to notifications topic automatically
      socket.send(JSON.stringify({ action: "subscribe", topic: "notifications" }));
    };

    socket.onmessage = async (event) => {
      try {
        const payload = JSON.parse(event.data);
        const { topic, data, event: eventType } = payload;
        
        // Handle queries invalidation on real-time events
        if (topic === "metrics") {
          queryClient.setQueryData(["dashboard-metrics"], data);
        } else if (topic === "observability") {
          // Data from WS might be wrapped or just the direct payload
          // Usually we need the activeOrgId to update the correct cache key, but if we don't have it here easily,
          // we can just update all matching queries, or get it from store
          const { useOrgStore } = await import("../store/useOrgStore");
          const activeOrgId = useOrgStore.getState().activeOrgId;
          if (activeOrgId) {
            queryClient.setQueryData(["observability-metrics", activeOrgId], data);
          }
        } else if (topic === "notifications") {
          const { toast } = await import("../store/useNotification");
          const alertType = data?.type || "info";
          if (alertType === "job_failed" || alertType === "worker_offline") {
            toast.error(data?.title || "Alert", data?.message || "");
          } else if (alertType === "high_failure_rate") {
            toast.warning(data?.title || "Warning", data?.message || "");
          } else {
            toast.info(data?.title || "Notification", data?.message || "");
          }
        } else if (topic === "jobs" || eventType === "job_updated") {
          queryClient.invalidateQueries({ queryKey: ["jobs"] });
        } else if (topic === "workers" || eventType === "worker_heartbeat") {
          queryClient.invalidateQueries({ queryKey: ["workers"] });
        }
        
      } catch (e) {
        console.error("Error parsing socket message", e);
      }
    };

    socket.onclose = () => {
      setConnected(false);
      console.log("WebSocket closed.");
      // Attempt reconnect after 5s
      setTimeout(() => {
        if (useAuth.getState().token) {
          // Re-trigger effect by checking auth token
        }
      }, 5000);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error", err);
    };

    return () => {
      socket.close();
    };
  }, [token, wsUrl, queryClient]);

  const subscribe = (topic: string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ action: "subscribe", topic }));
    }
  };

  const unsubscribe = (topic: string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ action: "unsubscribe", topic }));
    }
  };

  return (
    <SocketContext.Provider value={{ connected, subscribe, unsubscribe }}>
      {children}
    </SocketContext.Provider>
  );
}
