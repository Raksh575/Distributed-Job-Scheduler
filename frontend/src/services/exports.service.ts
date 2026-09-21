import api from "./api";

const exportsService = {
  downloadQueuesCSV: async (orgId: string): Promise<void> => {
    const response = await api.get(
      `/organizations/${orgId}/exports/queues`,
      { responseType: "blob" }
    );
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `queues_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  downloadWorkersCSV: async (orgId: string): Promise<void> => {
    const response = await api.get(
      `/organizations/${orgId}/exports/workers`,
      { responseType: "blob" }
    );
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `workers_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  downloadExecutionsCSV: async (orgId: string): Promise<void> => {
    const response = await api.get(
      `/organizations/${orgId}/exports/executions`,
      { responseType: "blob" }
    );
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `executions_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default exportsService;
