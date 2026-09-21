import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import queuesService, { QueueCreate } from "../services/queues.service";
import { toast } from "../store/useNotification";
import { extractApiError } from "../services/api";

export const useQueues = (orgId: string | null, projectId: string | null) => {
  return useQuery({
    queryKey: ["queues", orgId, projectId],
    queryFn: () => queuesService.listQueues(orgId!, projectId!),
    enabled: !!orgId && !!projectId,
    staleTime: 10000,
  });
};

export const useQueueStats = (orgId: string | null, queueId: string | null) => {
  return useQuery({
    queryKey: ["queue-stats", orgId, queueId],
    queryFn: () => queuesService.getQueueStats(orgId!, queueId!),
    enabled: !!orgId && !!queueId,
    refetchInterval: 8000,
  });
};

export const useCreateQueue = (orgId: string | null, projectId: string | null) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: QueueCreate) => {
      if (!orgId || !projectId) {
        return Promise.reject(new Error("No project available. Please create a project first or wait for data to load."));
      }
      return queuesService.createQueue(orgId, projectId, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queues", orgId, projectId] });
      toast.success("Queue created", "Your new queue is ready to receive jobs.");
    },
    onError: (err: unknown) => {
      toast.error("Failed to create queue", extractApiError(err));
    },
  });
};

export const usePauseQueue = (orgId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (queueId: string) => queuesService.pauseQueue(orgId, queueId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queues", orgId] });
      toast.info("Queue paused", "Job processing has been suspended.");
    },
    onError: (err: unknown) => {
      toast.error("Pause failed", extractApiError(err));
    },
  });
};

export const useResumeQueue = (orgId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (queueId: string) => queuesService.resumeQueue(orgId, queueId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queues", orgId] });
      toast.success("Queue resumed", "Job processing has been restored.");
    },
    onError: (err: unknown) => {
      toast.error("Resume failed", extractApiError(err));
    },
  });
};

export const useDeleteQueue = (orgId: string, projectId: string | null) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (queueId: string) => queuesService.deleteQueue(orgId, queueId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queues", orgId, projectId] });
      toast.success("Queue deleted");
    },
    onError: (err: unknown) => {
      toast.error("Delete failed", extractApiError(err));
    },
  });
};
