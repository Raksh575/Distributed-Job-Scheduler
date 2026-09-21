export type JobStatus = "queued" | "running" | "success" | "failed" | "cancelled";

export interface Job {
  id: string;
  name: string;
  queue: string;
  status: JobStatus;
  payload: Record<string, any>;
  result?: Record<string, any>;
  progress: number; // 0 to 100
  errorMessage?: string;
  startedAt?: string;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
  retries: number;
  maxRetries: number;
  parentId?: string;
}

export type WorkerStatus = "active" | "idle" | "offline";

export interface WorkerInfo {
  id: string;
  name: string;
  queue: string;
  status: WorkerStatus;
  currentJobId?: string;
  completedJobsCount: number;
  failedJobsCount: number;
  cpuUsage: number;
  memoryUsage: number;
  lastHeartbeat: string;
}

export interface ScheduledJob {
  id: string;
  name: string;
  triggerType: "cron" | "interval" | "date";
  cronExpression?: string;
  intervalSeconds?: number;
  nextRunTime?: string;
  isActive: boolean;
  targetQueue: string;
  createdAt: string;
}
