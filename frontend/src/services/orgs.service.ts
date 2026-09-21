import api from "./api";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo?: string;
  plan: string;
  status: string;
  created_at: string;
  version: number;
}

export interface Project {
  id: string;
  name: string;
  slug: string;
  description?: string;
  environment: string;
  status: string;
  organization_id: string;
  created_at: string;
}

export interface Member {
  id: string;
  user_id: string;
  organization_id: string;
  role: "Super Admin" | "Organization Admin" | "Developer" | "Viewer";
  created_at: string;
}

const orgsService = {
  getMyOrgs: async (): Promise<Organization[]> => {
    const response = await api.get<Organization[]>("/users/me/organizations");
    return response.data;
  },

  createOrg: async (payload: Partial<Organization>): Promise<Organization> => {
    const response = await api.post<Organization>("/organizations", payload);
    return response.data;
  },

  getOrg: async (orgId: string): Promise<Organization> => {
    const response = await api.get<Organization>(`/organizations/${orgId}`);
    return response.data;
  },

  updateOrg: async (orgId: string, payload: Partial<Organization>): Promise<Organization> => {
    const response = await api.patch<Organization>(`/organizations/${orgId}`, payload);
    return response.data;
  },

  deleteOrg: async (orgId: string): Promise<void> => {
    await api.delete(`/organizations/${orgId}`);
  },

  listProjects: async (orgId: string): Promise<Project[]> => {
    const response = await api.get<Project[]>(`/organizations/${orgId}/projects`);
    return response.data;
  },

  createProject: async (orgId: string, payload: Partial<Project>): Promise<Project> => {
    const response = await api.post<Project>(`/organizations/${orgId}/projects`, payload);
    return response.data;
  },
  
  updateProject: async (orgId: string, projectId: string, payload: Partial<Project>): Promise<Project> => {
    const response = await api.patch<Project>(`/organizations/${orgId}/projects/${projectId}`, payload);
    return response.data;
  },

  getMembers: async (orgId: string): Promise<Member[]> => {
    const response = await api.get<Member[]>(`/organizations/${orgId}/members`);
    return response.data;
  },

  inviteMember: async (orgId: string, email: string, role: string): Promise<Member> => {
    const response = await api.post<Member>(`/organizations/${orgId}/members`, { email, role });
    return response.data;
  },

  removeMember: async (orgId: string, memberId: string): Promise<void> => {
    await api.delete(`/organizations/${orgId}/members/${memberId}`);
  },
};

export default orgsService;
