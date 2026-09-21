import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import {
  Play, CheckCircle2, AlertTriangle, Clock,
  Server, Layers, Cpu, MemoryStick, Download, RefreshCw
} from "lucide-react";
import { useOrgStore } from "../store/useOrgStore";
import { useObservabilityMetrics } from "../hooks/useMetrics";
import { MetricCard } from "../components/shared/MetricCard";
import { GlassCard } from "../components/shared/GlassCard";
import { StatusBadge } from "../components/shared/StatusBadge";
import { PageHeader } from "../components/shared/PageHeader";
import { SkeletonMetrics } from "../components/shared/SkeletonCard";
import { ErrorState } from "../components/shared/EmptyState";
import exportsService from "../services/exports.service";
import { toast } from "../store/useNotification";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card px-3 py-2.5 rounded-xl text-xs shadow-2xl border border-white/8">
      <p className="text-slate-400 mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="font-semibold" style={{ color: entry.color }}>
          {entry.name}: <span className="font-mono">{entry.value}</span>
        </p>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const { activeOrgId } = useOrgStore();
  const { data, isLoading, isError, refetch } = useObservabilityMetrics(activeOrgId, 10000);

  const metrics = data?.system_metrics;
  const queueAnalytics = data?.queue_analytics ?? [];
  const workerAnalytics = data?.worker_analytics ?? [];

  // Build chart data from queue analytics
  const queueChartData = useMemo(() =>
    queueAnalytics.slice(0, 8).map(q => ({
      name: q.queue_name.length > 12 ? q.queue_name.slice(0, 12) + "…" : q.queue_name,
      size: q.queue_size,
      wait: Math.round(q.avg_wait_seconds),
      exec: Math.round(q.avg_execution_ms),
    })),
    [queueAnalytics]
  );

  const workerChartData = useMemo(() =>
    workerAnalytics.map(w => ({
      name: w.name.length > 14 ? w.name.slice(0, 14) + "…" : w.name,
      cpu: Math.round(w.cpu_usage),
      memory: Math.round(w.memory_usage),
      jobs: w.active_jobs,
    })),
    [workerAnalytics]
  );

  const handleDownload = async (type: "queues" | "workers" | "executions") => {
    if (!activeOrgId) return;
    try {
      await exportsService[`download${type.charAt(0).toUpperCase() + type.slice(1) as "Queues" | "Workers" | "Executions"}CSV`](activeOrgId);
      toast.success("Download started", `${type} report is downloading.`);
    } catch {
      toast.error("Download failed", "Could not generate the report.");
    }
  };

  if (isError) return <ErrorState title="Failed to load metrics" description="Could not connect to the backend observability service." action={<button onClick={() => refetch()} className="btn-primary px-4 py-2 rounded-xl text-sm text-white">Retry</button>} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Overview"
        subtitle="Real-time distributed cluster telemetry"
        icon={Layers}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="btn-ghost px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-white flex items-center gap-1.5"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </button>
            <div className="relative group">
              <button className="btn-ghost px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-white flex items-center gap-1.5">
                <Download className="h-3.5 w-3.5" />
                Export
              </button>
              <div className="absolute right-0 top-full mt-1 w-44 glass-card rounded-xl py-1 shadow-2xl hidden group-hover:block z-20">
                {(["queues", "workers", "executions"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => handleDownload(t)}
                    className="w-full text-left px-4 py-2 text-xs text-slate-300 hover:text-white hover:bg-white/5 capitalize transition-colors"
                  >
                    {t} CSV
                  </button>
                ))}
              </div>
            </div>
          </div>
        }
      />

      {/* KPI Metrics */}
      {isLoading ? (
        <SkeletonMetrics />
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Running Jobs"    value={metrics?.running_jobs ?? 0}  icon={Play}         iconColor="text-amber-400"   iconBg="bg-amber-500/10" />
          <MetricCard label="Queued Jobs"     value={metrics?.waiting_jobs ?? 0}  icon={Clock}        iconColor="text-blue-400"    iconBg="bg-blue-500/10" />
          <MetricCard label="Completed"       value={metrics?.success_jobs ?? 0}  icon={CheckCircle2} iconColor="text-emerald-400" iconBg="bg-emerald-500/10" />
          <MetricCard label="Failed Jobs"     value={metrics?.failed_jobs ?? 0}   icon={AlertTriangle} iconColor="text-red-400"   iconBg="bg-red-500/10" />
          <MetricCard label="Active Workers"  value={`${metrics?.active_workers ?? 0}`} icon={Server} iconColor="text-purple-400" iconBg="bg-purple-500/10" />
          <MetricCard label="Active Queues"   value={metrics?.active_queues ?? 0} icon={Layers}       iconColor="text-cyan-400"   iconBg="bg-cyan-500/10" />
          <MetricCard label="CPU Usage"       value={`${Math.round(metrics?.cpu_usage ?? 0)}`} suffix="%" icon={Cpu} iconColor="text-orange-400" iconBg="bg-orange-500/10" />
          <MetricCard label="Memory Usage"    value={`${Math.round(metrics?.memory_usage ?? 0)}`} suffix="%" icon={MemoryStick} iconColor="text-pink-400" iconBg="bg-pink-500/10" />
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Queue Analytics */}
        <GlassCard>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-bold text-white">Queue Analytics</h3>
              <p className="text-xs text-slate-400 mt-0.5">Job distribution across queues</p>
            </div>
          </div>
          <div className="h-64">
            {queueChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={queueChartData} barSize={24} barGap={8}>
                  <defs>
                    <linearGradient id="gradQueue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4FACFE" stopOpacity={0.9} />
                      <stop offset="95%" stopColor="#00F2FE" stopOpacity={0.2} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} width={30} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                  <Bar dataKey="size" name="Queue Size" fill="url(#gradQueue)" radius={[6,6,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm font-medium">No queue data yet</div>
            )}
          </div>
        </GlassCard>

        {/* Worker Utilization */}
        <GlassCard>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-bold text-white">Worker Utilization</h3>
              <p className="text-xs text-slate-400 mt-0.5">CPU & memory per active worker</p>
            </div>
          </div>
          <div className="h-64">
            {workerChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={workerChartData} barSize={12} barGap={6}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} width={30} unit="%" />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                  <Legend wrapperStyle={{ fontSize: "11px", color: "#94a3b8", fontWeight: 500 }} />
                  <Bar dataKey="cpu" name="CPU %" fill="#4FACFE" radius={[4,4,0,0]} />
                  <Bar dataKey="memory" name="RAM %" fill="#26D0CE" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">No worker data yet</div>
            )}
          </div>
        </GlassCard>
      </div>

      {/* Worker Health Grid */}
      {workerAnalytics.length > 0 && (
        <GlassCard>
          <h3 className="text-base font-bold text-white mb-5">Active Nodes</h3>
          <div className="divide-y divide-white/[0.04]">
            {workerAnalytics.map((worker) => (
              <motion.div
                key={worker.worker_id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-4 py-3 first:pt-0 last:pb-0"
              >
                <div className={`h-2.5 w-2.5 rounded-full shrink-0 ${worker.status === "active" ? "bg-emerald-400 animate-pulse" : worker.status === "idle" ? "bg-slate-400" : "bg-red-400"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">{worker.name}</p>
                  <p className="text-xs text-slate-500">{worker.active_jobs} active job{worker.active_jobs !== 1 ? "s" : ""}</p>
                </div>
                <div className="flex items-center gap-6 text-xs font-mono">
                  <div className="text-center hidden sm:block">
                    <p className="text-slate-500 text-[10px] uppercase tracking-wider">CPU</p>
                    <p className="text-white font-semibold">{Math.round(worker.cpu_usage)}%</p>
                  </div>
                  <div className="text-center hidden sm:block">
                    <p className="text-slate-500 text-[10px] uppercase tracking-wider">RAM</p>
                    <p className="text-white font-semibold">{Math.round(worker.memory_usage)}%</p>
                  </div>
                  <StatusBadge status={worker.status as any} pulse size="sm" />
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
}
