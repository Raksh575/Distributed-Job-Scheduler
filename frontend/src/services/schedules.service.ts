import api from "./api";

export interface ScheduledJobResponse {
  id: string;
  project_id: string;
  name: string;
  trigger_type: "cron" | "interval";
  cron_expression?: string;
  interval_seconds?: number;
  target_queue_id: string;
  job_name: string;
  job_payload: Record<string, any>;
  is_active: boolean;
  next_run_time?: string;
  created_at: string;
}

export interface ScheduledJobCreate {
  name: string;
  trigger_type: "cron" | "interval";
  cron_expression?: string;
  interval_seconds?: number;
  target_queue_id: string;
  job_name: string;
  job_payload: Record<string, any>;
}

const schedulesService = {
  listSchedules: async (orgId: string, projectId: string): Promise<ScheduledJobResponse[]> => {
    const response = await api.get<ScheduledJobResponse[]>(
      `/organizations/${orgId}/projects/${projectId}/schedules`
    );
    return response.data;
  },

  createSchedule: async (
    orgId: string,
    projectId: string,
    payload: ScheduledJobCreate
  ): Promise<ScheduledJobResponse> => {
    const response = await api.post<ScheduledJobResponse>(
      `/organizations/${orgId}/projects/${projectId}/schedules`,
      payload
    );
    return response.data;
  },

  pauseSchedule: async (orgId: string, scheduleId: string): Promise<ScheduledJobResponse> => {
    const response = await api.post<ScheduledJobResponse>(
      `/organizations/${orgId}/schedules/${scheduleId}/pause`
    );
    return response.data;
  },

  resumeSchedule: async (orgId: string, scheduleId: string): Promise<ScheduledJobResponse> => {
    const response = await api.post<ScheduledJobResponse>(
      `/organizations/${orgId}/schedules/${scheduleId}/resume`
    );
    return response.data;
  },

  deleteSchedule: async (orgId: string, scheduleId: string): Promise<void> => {
    await api.delete(`/organizations/${orgId}/schedules/${scheduleId}`);
  },
};

export default schedulesService;
