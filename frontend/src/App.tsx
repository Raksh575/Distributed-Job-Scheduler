import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuth } from "./store/useAuth";
import { SocketProvider } from "./contexts/SocketContext";
import DashboardLayout from "./layouts/DashboardLayout";

// Lazily import pages for optimal loading performance
import Dashboard from "./pages/Dashboard";
import Queues from "./pages/Queues";
import Jobs from "./pages/Jobs";
import JobDetails from "./pages/JobDetails";
import Workers from "./pages/Workers";
import DLQ from "./pages/DLQ";
import Settings from "./pages/Settings";
import Observability from "./pages/Observability";
import Simulator from "./pages/Simulator";
import Workflows from "./pages/Workflows";
import WorkflowDetails from "./pages/WorkflowDetails";
import AuditLogs from "./pages/AuditLogs";
import Scheduler from "./pages/Scheduler";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
});

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <DashboardLayout>{children}</DashboardLayout>;
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SocketProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Authentication Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />

            {/* Protected Workspace Layout Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/queues"
              element={
                <ProtectedRoute>
                  <Queues />
                </ProtectedRoute>
              }
            />
            <Route
              path="/jobs"
              element={
                <ProtectedRoute>
                  <Jobs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/jobs/:jobId"
              element={
                <ProtectedRoute>
                  <JobDetails />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workers"
              element={
                <ProtectedRoute>
                  <Workers />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dlq"
              element={
                <ProtectedRoute>
                  <DLQ />
                </ProtectedRoute>
              }
            />
            <Route
              path="/observability"
              element={
                <ProtectedRoute>
                  <Observability />
                </ProtectedRoute>
              }
            />
            <Route
              path="/simulator"
              element={
                <ProtectedRoute>
                  <Simulator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workflows"
              element={
                <ProtectedRoute>
                  <Workflows />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workflows/:workflowId"
              element={
                <ProtectedRoute>
                  <WorkflowDetails />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit-logs"
              element={
                <ProtectedRoute>
                  <AuditLogs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/schedules"
              element={
                <ProtectedRoute>
                  <Scheduler />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              }
            />

            {/* Catch-all fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </SocketProvider>
    </QueryClientProvider>
  );
}
