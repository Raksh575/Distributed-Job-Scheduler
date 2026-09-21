import api from "./api";

export interface QueueResponse {
  id: string;
  name: string;
  project_id: string;
  is_active: boolean;
  is_paused: boolean;
  priority: number;
  concurrency_limit: number;
  rate_limit?: number;
  created_at: string;
  updated_at: string;
}

export interface QueueCreate {
  name: string;
  priority?: number;
  concurrency_limit?: number;
  rate_limit?: number;
}

export interface QueueStats {
  total: number;
  queued: number;
  running: number;
  success: number;
  failed: number;
  cancelled: number;
}

const queuesService = {
  listQueues: async (orgId: string, projectId: string): Promise<QueueResponse[]> => {
    const response = await api.get<QueueResponse[]>(
      `/organizations/${orgId}/projects/${projectId}/queues`
    );
    return response.data;
  },

  createQueue: async (
    orgId: string,
    projectId: string,
    payload: QueueCreate
  ): Promise<QueueResponse> => {
    const response = await api.post<QueueResponse>(
      `/organizations/${orgId}/projects/${projectId}/queues`,
      payload
    );
    return response.data;
  },

  getQueueStats: async (orgId: string, queueId: string): Promise<QueueStats> => {
    const response = await api.get<QueueStats>(
      `/organizations/${orgId}/queues/${queueId}/stats`
    );
    return response.data;
  },

  pauseQueue: async (orgId: string, queueId: string): Promise<QueueResponse> => {
    const response = await api.post<QueueResponse>(
      `/organizations/${orgId}/queues/${queueId}/pause`
    );
    return response.data;
  },

  resumeQueue: async (orgId: string, queueId: string): Promise<QueueResponse> => {
    const response = await api.post<QueueResponse>(
      `/organizations/${orgId}/queues/${queueId}/resume`
    );
    return response.data;
  },

  deleteQueue: async (orgId: string, queueId: string): Promise<void> => {
    await api.delete(`/organizations/${orgId}/queues/${queueId}`);
  },
};

export default queuesService;
