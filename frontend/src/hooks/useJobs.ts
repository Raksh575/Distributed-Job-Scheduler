import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import jobsService, { JobCreate } from "../services/jobs.service";
import { toast } from "../store/useNotification";

export const useJobs = (orgId: string | null, queueId: string | null, skip = 0, limit = 50) => {
  return useQuery({
    queryKey: ["jobs", orgId, queueId, skip, limit],
    queryFn: () => jobsService.listJobs(orgId!, queueId!, skip, limit),
    enabled: !!orgId && !!queueId,
    staleTime: 5000,
    refetchInterval: 10000,
  });
};

export const useJobDetails = (orgId: string | null, jobId: string | null) => {
  return useQuery({
    queryKey: ["job", orgId, jobId],
    queryFn: () => jobsService.getJob(orgId!, jobId!),
    enabled: !!orgId && !!jobId,
    refetchInterval: 5000,
    staleTime: 2000,
  });
};

export const useJobLogs = (orgId: string | null, jobId: string | null) => {
  return useQuery({
    queryKey: ["job-logs", orgId, jobId],
    queryFn: () => jobsService.getJobLogs(orgId!, jobId!),
    enabled: !!orgId && !!jobId,
    refetchInterval: 5000,
  });
};

export const useSubmitJob = (orgId: string, queueId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: JobCreate) =>
      jobsService.submitJob(orgId, queueId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobs", orgId] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics", orgId] });
      toast.success("Job submitted", `Job "${data.name}" has been queued.`);
    },
    onError: (err: any) => {
      toast.error("Submit failed", err.response?.data?.error?.message || err.message);
    },
  });
};

export const useCancelJob = (orgId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => jobsService.cancelJob(orgId, jobId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobs", orgId] });
      queryClient.invalidateQueries({ queryKey: ["job", orgId, data.id] });
      toast.warning("Job cancelled", `Job "${data.name}" has been cancelled.`);
    },
    onError: (err: any) => {
      toast.error("Cancel failed", err.response?.data?.error?.message || err.message);
    },
  });
};

export const useReplayJob = (orgId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => jobsService.replayJob(orgId, jobId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobs", orgId] });
      queryClient.invalidateQueries({ queryKey: ["dlq", orgId] });
      toast.success("Job replayed", `Job "${data.name}" has been re-queued.`);
    },
    onError: (err: any) => {
      toast.error("Replay failed", err.response?.data?.error?.message || err.message);
    },
  });
};
