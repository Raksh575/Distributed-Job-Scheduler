import api from './api';
import { JobResponse } from './jobs.service';

export interface WorkflowNodeCreate {
  temp_id: string;
  name: string;
  queue_id: string;
  payload: Record<string, any>;
  dependencies: string[]; // temp_ids
  priority: number;
  max_retries: number;
}

export interface WorkflowCreate {
  name: string;
  nodes: WorkflowNodeCreate[];
}

export interface WorkflowResponse {
  id: string;
  project_id: string;
  name: string;
  status: 'running' | 'success' | 'failed' | 'cancelled';
  created_at: string;
  jobs: JobResponse[];
}

class WorkflowsService {
  async listWorkflows(orgId: string, projectId: string): Promise<WorkflowResponse[]> {
    const { data } = await api.get(`/${orgId}/projects/${projectId}/workflows`);
    return data;
  }

  async getWorkflow(orgId: string, workflowId: string): Promise<WorkflowResponse> {
    const { data } = await api.get(`/${orgId}/workflows/${workflowId}`);
    return data;
  }

  async createWorkflow(orgId: string, projectId: string, payload: WorkflowCreate): Promise<WorkflowResponse> {
    const { data } = await api.post(`/${orgId}/projects/${projectId}/workflows`, payload);
    return data;
  }

  async cancelWorkflow(orgId: string, workflowId: string): Promise<WorkflowResponse> {
    const { data } = await api.post(`/${orgId}/workflows/${workflowId}/cancel`);
    return data;
  }

  async retryWorkflow(orgId: string, workflowId: string): Promise<WorkflowResponse> {
    const { data } = await api.post(`/${orgId}/workflows/${workflowId}/retry`);
    return data;
  }
}

export const workflowsService = new WorkflowsService();
