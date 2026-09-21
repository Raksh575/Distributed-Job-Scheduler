import { useQuery } from "@tanstack/react-query";
import metricsService from "../services/metrics.service";

export const useObservabilityMetrics = (orgId: string | null, refetchInterval = 60000) => {
  return useQuery({
    queryKey: ["observability-metrics", orgId],
    queryFn: () => metricsService.getObservabilityMetrics(orgId!),
    enabled: !!orgId,
    refetchInterval,
    staleTime: Infinity,
  });
};

export const useDashboardMetrics = (orgId: string | null, refetchInterval = 60000) => {
  return useQuery({
    queryKey: ["dashboard-metrics", orgId],
    queryFn: () => metricsService.getDashboardMetrics(orgId!),
    enabled: !!orgId,
    refetchInterval,
    staleTime: 8000,
  });
};

export const useQueueTelemetry = (orgId: string | null, refetchInterval = 10000) => {
  return useQuery({
    queryKey: ["queue-telemetry", orgId],
    queryFn: () => metricsService.getQueueTelemetry(orgId!),
    enabled: !!orgId,
    refetchInterval,
    staleTime: 5000,
  });
};

export const useLogs = (
  orgId: string | null,
  params?: {
    category?: string;
    level?: string;
    search_query?: string;
    skip?: number;
    limit?: number;
  }
) => {
  return useQuery({
    queryKey: ["logs", orgId, params],
    queryFn: () => metricsService.getLogs(orgId!, params),
    enabled: !!orgId,
    refetchInterval: 8000,
    staleTime: 4000,
  });
};
