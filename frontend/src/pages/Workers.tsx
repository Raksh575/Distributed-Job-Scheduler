import { motion } from "framer-motion";
import { Cpu, Clock, Server } from "lucide-react";
import { useOrgStore } from "../store/useOrgStore";
import { useObservabilityMetrics } from "../hooks/useMetrics";
import { GlassCard } from "../components/shared/GlassCard";
import { StatusBadge } from "../components/shared/StatusBadge";
import { PageHeader } from "../components/shared/PageHeader";
import { EmptyState } from "../components/shared/EmptyState";
import { SkeletonCard } from "../components/shared/SkeletonCard";
import { ErrorState } from "../components/shared/EmptyState";

function CircleGauge({ value, color, size = 52 }: { value: number; color: string; size?: number }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6} />
      <circle
        cx={size / 2} cy={size / 2} r={radius} fill="none"
        stroke={color} strokeWidth={6}
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1)" }}
      />
    </svg>
  );
}

function formatLastSeen(isoDate: string) {
  const diff = Date.now() - new Date(isoDate).getTime();
  if (diff < 5000) return "Just now";
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  return new Date(isoDate).toLocaleTimeString();
}

export default function Workers() {
  const { activeOrgId } = useOrgStore();
  const { data, isLoading, isError } = useObservabilityMetrics(activeOrgId, 8000);

  const workers = data?.worker_analytics ?? [];

  if (isError) return <ErrorState title="Failed to load workers" />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workers"
        subtitle="Distributed task processor nodes and their health"
        icon={Cpu}
        actions={
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-lg">
              {workers.filter(w => w.status === "active").length} Active
            </span>
            <span className="text-xs font-semibold text-slate-400 bg-white/5 border border-white/8 px-2.5 py-1 rounded-lg">
              {workers.length} Total
            </span>
          </div>
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} rows={4} />)}
        </div>
      ) : workers.length === 0 ? (
        <EmptyState
          icon={Server}
          title="No workers online"
          description="Start a worker node to begin processing jobs. Run: python -m app.workers.runner"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {workers.map((worker, i) => (
            <motion.div
              key={worker.worker_id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
            >
              <GlassCard interactive gradient>
                {/* Worker Header */}
                <div className="flex items-start justify-between mb-5">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-bold text-white truncate">{worker.name}</h3>
                    <p className="text-[10px] font-mono text-slate-500 truncate mt-0.5">{worker.worker_id}</p>
                  </div>
                  <StatusBadge status={worker.status as any} pulse size="sm" />
                </div>

                {/* CPU / RAM Gauges */}
                <div className="flex items-center justify-around mb-5">
                  <div className="flex flex-col items-center gap-2">
                    <div className="relative">
                      <CircleGauge value={Math.round(worker.cpu_usage)} color="#4FACFE" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-[10px] font-bold text-white">{Math.round(worker.cpu_usage)}%</span>
                      </div>
                    </div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">CPU</p>
                  </div>
                  <div className="flex flex-col items-center gap-2">
                    <div className="relative">
                      <CircleGauge value={Math.round(worker.memory_usage)} color="#26D0CE" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-[10px] font-bold text-white">{Math.round(worker.memory_usage)}%</span>
                      </div>
                    </div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">RAM</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-white font-mono">{worker.active_jobs}</p>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">Jobs</p>
                  </div>
                </div>

                {/* Last heartbeat */}
                <div className="flex items-center justify-between pt-3 border-t border-white/5 text-xs">
                  <div className="flex items-center gap-1.5 text-slate-500">
                    <Clock className="h-3 w-3" />
                    <span>Last seen</span>
                  </div>
                  <span className={`font-medium ${worker.status === "offline" ? "text-red-400" : "text-slate-300"}`}>
                    {formatLastSeen(worker.last_heartbeat)}
                  </span>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
