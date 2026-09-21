import { useState, useEffect, useMemo } from "react";
import { Server, Activity, Database, CheckCircle, XCircle, Clock, Users } from "lucide-react";
import { useOrgStore } from "../store/useOrgStore";
import { useObservabilityMetrics, useLogs } from "../hooks/useMetrics";
import { useSocket } from "../contexts/SocketContext";
import { PageHeader } from "../components/shared/PageHeader";
import { SkeletonMetrics } from "../components/shared/SkeletonCard";
import { AnimatedKPICard } from "../components/observability/AnimatedKPICard";
import { MemoizedAreaChart } from "../components/observability/MetricCharts";
import { LiveHeatmap } from "../components/observability/LiveHeatmap";
import { ActivityTimeline, TimelineEvent } from "../components/observability/ActivityTimeline";

const MAX_HISTORY = 30; // Store last 30 data points for charts

export default function Observability() {
  const { activeOrgId } = useOrgStore();
  const { subscribe, unsubscribe, connected } = useSocket();

  const { data, isLoading } = useObservabilityMetrics(activeOrgId);
  const { data: logsData } = useLogs(activeOrgId, { limit: 20 });

  // History states for charts
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    if (activeOrgId) {
      subscribe("observability");
      return () => unsubscribe("observability");
    }
  }, [activeOrgId, subscribe, unsubscribe]);

  useEffect(() => {
    if (data) {
      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
      
      setHistory(prev => {
        const newPoint = {
          time: timeStr,
          cpu: data.system_metrics?.cpu_usage || 0,
          memory: data.system_metrics?.memory_usage || 0,
          running: data.system_metrics?.running_jobs || 0,
          waiting: data.system_metrics?.waiting_jobs || 0,
          success: data.system_metrics?.success_jobs || 0,
          failed: data.system_metrics?.failed_jobs || 0,
        };
        const next = [...prev, newPoint];
        if (next.length > MAX_HISTORY) return next.slice(next.length - MAX_HISTORY);
        return next;
      });
    }
  }, [data]);

  const sys = data?.system_metrics;
  const queues = data?.queue_analytics ?? [];
  const workers = data?.worker_analytics ?? [];

  const uptime = sys?.uptime_seconds;
  const uptimeStr = uptime ? `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m` : "—";

  // Derived metrics
  const totalJobs = (sys?.success_jobs || 0) + (sys?.failed_jobs || 0);
  const successRate = totalJobs > 0 ? ((sys?.success_jobs || 0) / totalJobs) * 100 : 100;
  
  // Heatmap nodes
  const workerNodes = useMemo(() => workers.map(w => ({
    id: w.worker_id,
    name: w.name,
    value: Math.max(w.cpu_usage, w.memory_usage) / 100,
    status: (w.status === 'active' ? (w.cpu_usage > 80 ? 'warning' : 'success') : 'offline') as any
  })), [workers]);

  const queueNodes = useMemo(() => queues.map(q => ({
    id: q.queue_id,
    name: q.queue_name,
    value: Math.min(q.queue_size / 1000, 1),
    status: (q.is_active ? (q.queue_size > 500 ? 'warning' : 'success') : 'offline') as any
  })), [queues]);

  // Timeline events from logs
  const timelineEvents = useMemo<TimelineEvent[]>(() => {
    if (!logsData?.logs) return [];
    return logsData.logs.map((l, i) => ({
      id: `${l.timestamp}-${i}`,
      time: new Date(l.timestamp).toLocaleTimeString(),
      type: l.level === 'error' ? 'error' : l.level === 'warning' ? 'warning' : l.level === 'info' ? 'success' : 'info',
      title: l.level,
      description: l.message
    }));
  }, [logsData]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Enterprise Observability"
        subtitle={`Live telemetry, heatmaps, and system health (Uptime: ${uptimeStr})`}
        icon={Activity}
        actions={
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 'bg-rose-500'}`} />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">{connected ? 'Live' : 'Disconnected'}</span>
            </div>
          </div>
        }
      />

      {isLoading && history.length === 0 ? (
        <SkeletonMetrics />
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <AnimatedKPICard label="System CPU" value={`${sys?.cpu_usage?.toFixed(1) || 0}`} suffix="%" icon={Server} iconColor="text-blue-400" iconBg="bg-blue-500/10" trend={{ value: 2.1, isPositive: false }} />
            <AnimatedKPICard label="Memory Load" value={`${sys?.memory_usage?.toFixed(1) || 0}`} suffix="%" icon={Database} iconColor="text-purple-400" iconBg="bg-purple-500/10" trend={{ value: 0.5, isPositive: true }} />
            <AnimatedKPICard label="Active Workers" value={sys?.active_workers || 0} icon={Users} iconColor="text-emerald-400" iconBg="bg-emerald-500/10" />
            <AnimatedKPICard label="Running Jobs" value={sys?.running_jobs || 0} icon={Activity} iconColor="text-amber-400" iconBg="bg-amber-500/10" />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <AnimatedKPICard label="Queued Jobs" value={sys?.waiting_jobs || 0} icon={Clock} iconColor="text-slate-400" iconBg="bg-slate-500/10" />
            <AnimatedKPICard label="Success Rate" value={successRate.toFixed(1)} suffix="%" icon={CheckCircle} iconColor="text-emerald-400" iconBg="bg-emerald-500/10" />
            <AnimatedKPICard label="Failed Jobs" value={sys?.failed_jobs || 0} icon={XCircle} iconColor="text-rose-400" iconBg="bg-rose-500/10" />
            <AnimatedKPICard label="DB Connections" value={sys?.database_connections || 0} icon={Database} iconColor="text-blue-400" iconBg="bg-blue-500/10" />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <MemoizedAreaChart 
              title="System Resource Utilization"
              data={history}
              dataKeys={["cpu", "memory"]}
              colors={["#3b82f6", "#a855f7"]}
            />
            <MemoizedAreaChart 
              title="Job Throughput"
              data={history}
              dataKeys={["running", "waiting"]}
              colors={["#10b981", "#f59e0b"]}
            />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-12">
            <div className="xl:col-span-2 space-y-6">
              <LiveHeatmap title="Worker Health Matrix" nodes={workerNodes} />
              <LiveHeatmap title="Queue Saturation Heatmap" nodes={queueNodes} />
            </div>
            <div className="h-[600px]">
              <ActivityTimeline title="Live Activity Log" events={timelineEvents} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
