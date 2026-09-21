import api from "./api";

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  database_connections: number;
  active_workers: number;
  active_queues: number;
  running_jobs: number;
  waiting_jobs: number;
  failed_jobs: number;
  success_jobs: number;
  uptime_seconds: number;
}

export interface QueueAnalytic {
  queue_id: string;
  queue_name: string;
  queue_size: number;
  avg_wait_seconds: number;
  avg_execution_ms: number;
  is_active: boolean;
}

export interface WorkerAnalytic {
  worker_id: string;
  name: string;
  status: "active" | "idle" | "offline";
  cpu_usage: number;
  memory_usage: number;
  active_jobs: number;
  last_heartbeat: string;
}

export interface ObservabilityMetrics {
  system_metrics: SystemMetrics;
  queue_analytics: QueueAnalytic[];
  worker_analytics: WorkerAnalytic[];
}

export interface DashboardMetrics {
  active_workers: number;
  total_queues: number;
  running_jobs: number;
  queued_jobs: number;
  completed_jobs_today: number;
  failed_jobs: number;
  success_rate: number;
  avg_execution_ms: number;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  category?: string;
  name?: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
  skip: number;
  limit: number;
}

export interface QueueTelemetry {
  queue_id: string;
  queue_name: string;
  pending_count: number;
  running_count: number;
}

const metricsService = {
  getDashboardMetrics: async (orgId: string): Promise<DashboardMetrics> => {
    const response = await api.get<DashboardMetrics>(
      `/organizations/${orgId}/dashboard-metrics`
    );
    return response.data;
  },

  getObservabilityMetrics: async (orgId: string): Promise<ObservabilityMetrics> => {
    const response = await api.get<ObservabilityMetrics>(
      `/organizations/${orgId}/observability/metrics`
    );
    return response.data;
  },

  getLogs: async (
    orgId: string,
    params?: {
      category?: string;
      level?: string;
      search_query?: string;
      skip?: number;
      limit?: number;
    }
  ): Promise<LogsResponse> => {
    const response = await api.get<LogsResponse>(
      `/organizations/${orgId}/observability/logs`,
      { params }
    );
    return response.data;
  },

  getQueueTelemetry: async (orgId: string): Promise<QueueTelemetry[]> => {
    const response = await api.get<QueueTelemetry[]>(
      `/organizations/${orgId}/queues-telemetry`
    );
    return response.data;
  },
};

export default metricsService;
