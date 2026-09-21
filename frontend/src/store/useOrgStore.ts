import { create } from "zustand";
import api from "../services/api";

import { Organization } from "../services/orgs.service";

interface OrgState {
  organizations: Organization[];
  activeOrgId: string | null;
  activeOrg: Organization | null;
  isLoading: boolean;
  setOrganizations: (orgs: Organization[]) => void;
  setActiveOrgId: (id: string | null) => void;
  fetchOrganizations: () => Promise<void>;
  createOrganization: (payload: Partial<Organization>) => Promise<Organization>;
}

export const useOrgStore = create<OrgState>((set, get) => ({
  organizations: [],
  activeOrgId: localStorage.getItem("djs_active_org_id"),
  activeOrg: null,
  isLoading: false,

  setOrganizations: (organizations) => set({ organizations }),

  setActiveOrgId: (activeOrgId) => {
    if (activeOrgId) {
      localStorage.setItem("djs_active_org_id", activeOrgId);
      const activeOrg = get().organizations.find((o) => o.id === activeOrgId) || null;
      set({ activeOrgId, activeOrg });
    } else {
      localStorage.removeItem("djs_active_org_id");
      set({ activeOrgId: null, activeOrg: null });
    }
  },

  fetchOrganizations: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get<Organization[]>("/users/me/organizations");
      const organizations = response.data;
      
      let activeOrgId = get().activeOrgId;
      if (organizations.length > 0) {
        const exists = organizations.some((o) => o.id === activeOrgId);
        if (!exists) {
          activeOrgId = organizations[0].id;
        }
      } else {
        activeOrgId = null;
      }
      
      const activeOrg = activeOrgId
        ? organizations.find((o) => o.id === activeOrgId) || null
        : null;

      if (activeOrgId) {
        localStorage.setItem("djs_active_org_id", activeOrgId);
      } else {
        localStorage.removeItem("djs_active_org_id");
      }

      set({ organizations, activeOrgId, activeOrg });
    } catch (e) {
      console.error("Failed to fetch organizations", e);
    } finally {
      set({ isLoading: false });
    }
  },

  createOrganization: async (payload) => {
    const response = await api.post<Organization>("/organizations", payload);
    const newOrg = response.data;
    
    // Refresh the token to include the new organization's role in the JWT claims
    try {
      const refreshToken = localStorage.getItem("djs_refresh_token");
      if (refreshToken) {
        const refreshResponse = await api.post("/auth/refresh", { refresh_token: refreshToken });
        const { access_token, refresh_token: newRefreshToken } = refreshResponse.data;
        localStorage.setItem("djs_access_token", access_token);
        localStorage.setItem("djs_refresh_token", newRefreshToken);
      }
    } catch (err) {
      console.warn("Failed to refresh token after creating organization", err);
    }
    
    const currentOrgs = [...get().organizations, newOrg];
    set({ organizations: currentOrgs });
    get().setActiveOrgId(newOrg.id);
    return newOrg;
  }
}));
