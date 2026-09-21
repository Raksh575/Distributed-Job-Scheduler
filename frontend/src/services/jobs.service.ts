import api from "./api";

export type JobStatus = "queued" | "running" | "success" | "failed" | "cancelled" | "scheduled" | "claimed";

export interface JobResponse {
  id: string;
  name: string;
  queue_id: string;
  status: JobStatus;
  payload: Record<string, unknown>;
  result?: Record<string, unknown>;
  error_message?: string;
  progress: number;
  priority: number;
  max_retries: number;
  retries_count: number;
  timeout?: number;
  parent_id?: string;
  run_at?: string;
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  name: string;
  payload?: Record<string, unknown>;
  parent_id?: string;
  delay_seconds?: number;
  priority?: number;
  max_retries?: number;
  timeout?: number;
}

export interface JobLog {
  level: string;
  message: string;
  timestamp: string;
}

export interface AIFailureAnalysis {
  failure_summary: string;
  root_cause: string;
  error_category: string;
  confidence_score: number;
  suggested_fixes: string[];
  retry_recommendation: boolean;
  estimated_recovery: string;
}

export interface JobExecution {
  execution_id: string;
  worker_id: string | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  duration_ms: number | null;
  ai_analysis?: AIFailureAnalysis | null;
  logs: JobLog[];
}

const jobsService = {
  submitJob: async (
    orgId: string,
    queueId: string,
    payload: JobCreate
  ): Promise<JobResponse> => {
    const response = await api.post<JobResponse>(
      `/organizations/${orgId}/queues/${queueId}/jobs`,
      payload
    );
    return response.data;
  },

  getJob: async (orgId: string, jobId: string): Promise<JobResponse> => {
    const response = await api.get<JobResponse>(
      `/organizations/${orgId}/jobs/${jobId}`
    );
    return response.data;
  },

  listJobs: async (
    orgId: string,
    queueId: string,
    skip = 0,
    limit = 50
  ): Promise<JobResponse[]> => {
    const response = await api.get<JobResponse[]>(
      `/organizations/${orgId}/queues/${queueId}/jobs`,
      { params: { skip, limit } }
    );
    return response.data;
  },

  cancelJob: async (orgId: string, jobId: string): Promise<JobResponse> => {
    const response = await api.post<JobResponse>(
      `/organizations/${orgId}/jobs/${jobId}/cancel`
    );
    return response.data;
  },

  replayJob: async (orgId: string, jobId: string): Promise<JobResponse> => {
    const response = await api.post<JobResponse>(
      `/organizations/${orgId}/dlq/${jobId}/replay`
    );
    return response.data;
  },

  getJobLogs: async (orgId: string, jobId: string): Promise<JobExecution[]> => {
    const response = await api.get<JobExecution[]>(
      `/organizations/${orgId}/jobs/${jobId}/logs`
    );
    return response.data;
  },
};

export default jobsService;
