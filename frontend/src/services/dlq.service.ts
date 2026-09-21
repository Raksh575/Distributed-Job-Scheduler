import api from "./api";
import { JobResponse } from "./jobs.service";

export interface DLQRecord {
  id: string;
  job_id: string;
  failed_at: string;
  reason: string;
  job?: JobResponse;
}

const dlqService = {
  listDLQ: async (
    orgId: string,
    skip = 0,
    limit = 50
  ): Promise<DLQRecord[]> => {
    const response = await api.get<DLQRecord[]>(
      `/organizations/${orgId}/dlq`,
      { params: { skip, limit } }
    );
    return response.data;
  },

  replayJob: async (orgId: string, jobId: string): Promise<JobResponse> => {
    const response = await api.post<JobResponse>(
      `/organizations/${orgId}/dlq/${jobId}/replay`
    );
    return response.data;
  },

  deleteJob: async (orgId: string, jobId: string): Promise<void> => {
    await api.delete(`/organizations/${orgId}/dlq/${jobId}`);
  },
};

export default dlqService;
