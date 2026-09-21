import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft, RotateCcw, Ban, Clock,
  Cpu, Hash
} from "lucide-react";
import { useOrgStore } from "../store/useOrgStore";
import { useJobDetails, useJobLogs, useCancelJob, useReplayJob } from "../hooks/useJobs";
import { StatusBadge } from "../components/shared/StatusBadge";
import { GlassCard } from "../components/shared/GlassCard";
import { ConfirmDialog } from "../components/shared/ConfirmDialog";
import { SkeletonCard } from "../components/shared/SkeletonCard";
import { ErrorState } from "../components/shared/EmptyState";
import { AIFailureAnalysisCard } from "../components/shared/AIFailureAnalysisCard";

const LOG_COLORS: Record<string, string> = {
  error: "text-red-400",
  warning: "text-amber-400",
  info: "text-blue-300",
  debug: "text-slate-400",
};

function formatDuration(ms: number | null) {
  if (!ms) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export default function JobDetails() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { activeOrgId } = useOrgStore();
  const [cancelOpen, setCancelOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"logs" | "payload" | "result">("logs");

  const { data: job, isLoading, isError } = useJobDetails(activeOrgId, jobId ?? null);
  const { data: executions = [] } = useJobLogs(activeOrgId, jobId ?? null);
  const cancelJob = useCancelJob(activeOrgId!);
  const replayJob = useReplayJob(activeOrgId!);

  if (isLoading) return (
    <div className="space-y-6">
      <SkeletonCard rows={4} />
      <SkeletonCard rows={6} />
    </div>
  );

  if (isError || !job) return (
    <ErrorState
      title="Job not found"
      description="This job may have been deleted or you don't have access."
      action={<button onClick={() => navigate("/jobs")} className="btn-primary px-4 py-2 rounded-xl text-sm text-white">Back to Jobs</button>}
    />
  );

  const latestExecution = executions[0];
  const allLogs = executions.flatMap(e =>
    e.logs.map(l => ({ ...l, execution_id: e.execution_id }))
  );

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Back + Header */}
      <div>
        <button
          onClick={() => navigate("/jobs")}
          className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Jobs
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-white">{job.name}</h1>
              <StatusBadge status={job.status as any} pulse />
            </div>
            <p className="text-xs text-slate-500 font-mono mt-1">{job.id}</p>
          </div>
          <div className="flex gap-2 shrink-0">
            {(job.status === "failed" || job.status === "cancelled") && (
              <button
                onClick={() => replayJob.mutate(job.id)}
                disabled={replayJob.isPending}
                className="btn-ghost px-3 py-2 rounded-xl text-sm font-medium text-blue-400 flex items-center gap-1.5"
              >
                <RotateCcw className="h-4 w-4" /> Replay
              </button>
            )}
            {(job.status === "queued" || job.status === "running") && (
              <button
                onClick={() => setCancelOpen(true)}
                className="btn-danger px-3 py-2 rounded-xl text-sm font-medium flex items-center gap-1.5"
              >
                <Ban className="h-4 w-4" /> Cancel
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Priority", value: job.priority, icon: Hash },
          { label: "Retries", value: `${job.retries_count} / ${job.max_retries}`, icon: RotateCcw },
          { label: "Progress", value: `${job.progress}%`, icon: Cpu },
          { label: "Duration", value: formatDuration(latestExecution?.duration_ms ?? null), icon: Clock },
        ].map(({ label, value, icon: Icon }) => (
          <GlassCard key={label} padding="sm">
            <div className="flex items-center gap-2 mb-2">
              <Icon className="h-3.5 w-3.5 text-slate-500" />
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">{label}</p>
            </div>
            <p className="text-xl font-bold text-white font-mono">{value}</p>
          </GlassCard>
        ))}
      </div>

      {/* Progress bar */}
      {job.status === "running" && (
        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-1.5">
            <span>Execution Progress</span><span>{job.progress}%</span>
          </div>
          <div className="progress-bar">
            <motion.div
              className="progress-bar-fill"
              initial={{ width: 0 }}
              animate={{ width: `${job.progress}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
        </div>
      )}

      {/* Tabs */}
      <GlassCard padding="none">
        <div className="flex border-b border-white/5">
          {(["logs", "payload", "result"] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-3.5 text-xs font-semibold uppercase tracking-wider capitalize transition-all ${
                activeTab === tab
                  ? "text-blue-300 border-b-2 border-blue-400"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="p-5">
          {activeTab === "logs" && (
            <div className="log-terminal">
              {allLogs.length === 0 ? (
                <p className="text-slate-600">No log entries recorded yet.</p>
              ) : (
                allLogs.map((log, i) => (
                  <div key={i} className="flex gap-3 mb-1">
                    <span className="text-slate-600 shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    <span className={`uppercase text-[10px] font-bold shrink-0 w-12 ${LOG_COLORS[log.level] ?? "text-slate-400"}`}>{log.level}</span>
                    <span className={LOG_COLORS[log.level] ?? "text-slate-300"}>{log.message}</span>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "payload" && (
            <div className="log-terminal">
              <pre className="text-blue-300 text-xs leading-relaxed">
                {JSON.stringify(job.payload, null, 2)}
              </pre>
            </div>
          )}

          {activeTab === "result" && (
            <div className="log-terminal">
              {job.result ? (
                <pre className="text-emerald-300 text-xs leading-relaxed">
                  {JSON.stringify(job.result, null, 2)}
                </pre>
              ) : job.error_message ? (
                <pre className="text-red-400 text-xs leading-relaxed">{job.error_message}</pre>
              ) : (
                <p className="text-slate-600">No result data available yet.</p>
              )}
            </div>
          )}
        </div>
      </GlassCard>

      {/* AI Analysis (If Available) */}
      {executions.length > 0 && executions[0].ai_analysis && (
        <AIFailureAnalysisCard analysis={executions[0].ai_analysis} className="mb-6" />
      )}

      {/* Execution History */}
      {executions.length > 0 && (
        <GlassCard>
          <h3 className="text-sm font-bold text-white mb-4">Execution History</h3>
          <div className="space-y-3">
            {executions.map((exec, i) => (
              <div key={exec.execution_id} className="flex items-center gap-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <div className={`h-2 w-2 rounded-full shrink-0 ${exec.status === "success" ? "bg-emerald-400" : exec.status === "failed" ? "bg-red-400" : "bg-blue-400"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-white">Attempt #{executions.length - i}</p>
                  <p className="text-[10px] text-slate-500 font-mono">{exec.started_at}</p>
                </div>
                <StatusBadge status={exec.status as any} size="sm" />
                <span className="text-xs font-mono text-slate-400">{formatDuration(exec.duration_ms)}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      <ConfirmDialog
        open={cancelOpen}
        title="Cancel Job"
        description={`Are you sure you want to cancel "${job.name}"?`}
        confirmLabel="Cancel Job"
        variant="danger"
        isLoading={cancelJob.isPending}
        onConfirm={() => { cancelJob.mutate(job.id); setCancelOpen(false); }}
        onCancel={() => setCancelOpen(false)}
      />
    </div>
  );
}
