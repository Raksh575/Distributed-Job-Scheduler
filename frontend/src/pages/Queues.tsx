import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FolderSync, Plus, Play, Pause, Trash2, X, Loader2, RefreshCcw } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useOrgStore } from "../store/useOrgStore";
import { useQueues, useCreateQueue, usePauseQueue, useResumeQueue, useDeleteQueue } from "../hooks/useQueues";
import { GlassCard } from "../components/shared/GlassCard";
import { StatusBadge } from "../components/shared/StatusBadge";
import { PageHeader } from "../components/shared/PageHeader";
import { EmptyState } from "../components/shared/EmptyState";
import { ConfirmDialog } from "../components/shared/ConfirmDialog";
import { SkeletonCard } from "../components/shared/SkeletonCard";
import { QueueResponse } from "../services/queues.service";
import orgsService from "../services/orgs.service";
import { extractApiError } from "../services/api";

export default function Queues() {
  const { activeOrgId } = useOrgStore();
  const queryClient = useQueryClient();

  // Fetch projects to get a projectId for queue operations
  const { data: projects = [], isLoading: projectsLoading, refetch: refetchProjects } = useQuery({
    queryKey: ["projects", activeOrgId],
    queryFn: () => orgsService.listProjects(activeOrgId!),
    enabled: !!activeOrgId,
  });
  const projectId = projects[0]?.id ?? null;
  const [provisioningProject, setProvisioningProject] = useState(false);

  const handleProvisionProject = async () => {
    setProvisioningProject(true);
    try {
      // The backend auto-creates a Default project when list returns empty.
      // Invalidate the cache to force a fresh fetch which triggers auto-creation.
      await queryClient.invalidateQueries({ queryKey: ["projects", activeOrgId] });
      await refetchProjects();
    } finally {
      setProvisioningProject(false);
    }
  };

  const { data: queues = [], isLoading, isError } = useQueues(activeOrgId, projectId);
  const createQueue = useCreateQueue(activeOrgId, projectId);
  const pauseQueue = usePauseQueue(activeOrgId!);
  const resumeQueue = useResumeQueue(activeOrgId!);
  const deleteQueue = useDeleteQueue(activeOrgId!, projectId);

  const [showCreate, setShowCreate] = useState(false);
  const [newQueueName, setNewQueueName] = useState("");
  const [priority, setPriority] = useState(0);
  const [concurrencyLimit, setConcurrencyLimit] = useState(10);
  const [rateLimit, setRateLimit] = useState<number | "">("");
  const [deleteTarget, setDeleteTarget] = useState<QueueResponse | null>(null);
  const [createError, setCreateError] = useState("");

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQueueName.trim()) return;
    setCreateError("");
    try {
      await createQueue.mutateAsync({ 
        name: newQueueName.trim(),
        priority,
        concurrency_limit: concurrencyLimit,
        rate_limit: rateLimit === "" ? undefined : Number(rateLimit)
      });
      setNewQueueName(""); setPriority(0); setConcurrencyLimit(10); setRateLimit(""); setShowCreate(false);
    } catch (err: unknown) {
      setCreateError(extractApiError(err));
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Queues"
        subtitle="Manage job processing queues and their policies"
        icon={FolderSync}
        actions={
          <button
            onClick={() => setShowCreate(true)}
            disabled={!activeOrgId || !projectId}
            className="btn-primary px-5 py-2.5 rounded-xl text-sm font-bold text-white flex items-center gap-2 disabled:opacity-50 shadow-glow-primary"
          >
            <Plus className="h-4 w-4" /> New Queue
          </button>
        }
      />

      {isLoading || projectsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} rows={3} />)}
        </div>
      ) : isError ? (
        <div className="text-center text-slate-500 py-20">Failed to load queues.</div>
      ) : !projectId ? (
        <EmptyState
          icon={FolderSync}
          title="No project workspace"
          description="This organization doesn't have a project yet. Click below to automatically set up your default workspace."
          action={
            <button
              onClick={handleProvisionProject}
              disabled={provisioningProject || projectsLoading}
              className="btn-primary px-5 py-2.5 rounded-xl text-sm font-semibold text-white flex items-center gap-2 disabled:opacity-50"
            >
              {provisioningProject
                ? <><Loader2 className="h-4 w-4 animate-spin" /> Setting up workspace…</>
                : <><RefreshCcw className="h-4 w-4" /> Set Up Default Workspace</>}
            </button>
          }
        />
      ) : queues.length === 0 ? (
        <EmptyState
          icon={FolderSync}
          title="No queues yet"
          description="Create a queue to start routing jobs to workers."
          action={
            <button onClick={() => setShowCreate(true)} disabled={!projectId} className="btn-primary px-4 py-2 rounded-xl text-sm font-semibold text-white disabled:opacity-50">
              Create Queue
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {queues.map((queue, i) => (
            <motion.div
              key={queue.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <GlassCard interactive gradient className="group">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold text-white truncate">{queue.name}</h3>
                    <p className="text-[10px] font-mono text-slate-500 mt-0.5 truncate">{queue.id}</p>
                  </div>
                  <StatusBadge status={queue.is_active ? "active" : "paused"} pulse size="sm" />
                </div>

                <div className="grid grid-cols-3 gap-2 mt-4">
                  <div className="bg-white/5 rounded-lg p-2 text-center">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Priority</p>
                    <p className="text-sm font-semibold text-white">{queue.priority ?? 0}</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-2 text-center">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Concurrency</p>
                    <p className="text-sm font-semibold text-white">{queue.concurrency_limit ?? 10}</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-2 text-center">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Rate Limit</p>
                    <p className="text-sm font-semibold text-white">{queue.rate_limit ? `${queue.rate_limit}/s` : "None"}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-4 pt-4 border-t border-white/5">
                  {queue.is_active ? (
                    <button
                      onClick={() => pauseQueue.mutate(queue.id)}
                      disabled={pauseQueue.isPending}
                      className="btn-ghost flex-1 py-2 rounded-lg text-xs font-medium text-slate-300 flex items-center justify-center gap-1.5"
                    >
                      {pauseQueue.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Pause className="h-3.5 w-3.5" />}
                      Pause
                    </button>
                  ) : (
                    <button
                      onClick={() => resumeQueue.mutate(queue.id)}
                      disabled={resumeQueue.isPending}
                      className="btn-ghost flex-1 py-2 rounded-lg text-xs font-medium text-emerald-400 flex items-center justify-center gap-1.5"
                    >
                      {resumeQueue.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                      Resume
                    </button>
                  )}
                  <button
                    onClick={() => setDeleteTarget(queue)}
                    className="btn-danger p-2 rounded-lg text-xs"
                    title="Delete queue"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <AnimatePresence>
        {showCreate && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setShowCreate(false)} className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]" />
            <motion.div initial={{ opacity: 0, scale: 0.93 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.93 }}
              transition={{ type: "spring", stiffness: 350, damping: 28 }}
              className="fixed inset-0 z-[101] flex items-center justify-center p-4">
              <div className="glass-card gradient-border rounded-2xl p-6 w-full max-w-md">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="text-base font-bold text-white">Create Queue</h3>
                  <button onClick={() => setShowCreate(false)} className="text-slate-500 hover:text-white"><X className="h-4 w-4" /></button>
                </div>
                <form onSubmit={handleCreate} className="space-y-4">
                  {createError && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-400">{createError}</div>
                  )}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Queue Name</label>
                    <input
                      type="text" required value={newQueueName}
                      onChange={e => setNewQueueName(e.target.value.replace(/[^a-zA-Z0-9_-]/g, ""))}
                      placeholder="email-notifications"
                      className="glass-input w-full font-mono"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 mb-1.5">Priority (0-100)</label>
                      <input
                        type="number" min="0" max="100" value={priority}
                        onChange={e => setPriority(parseInt(e.target.value) || 0)}
                        className="glass-input w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 mb-1.5">Concurrency Limit</label>
                      <input
                        type="number" min="1" value={concurrencyLimit}
                        onChange={e => setConcurrencyLimit(parseInt(e.target.value) || 1)}
                        className="glass-input w-full"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Rate Limit (Jobs/s) (Optional)</label>
                    <input
                      type="number" min="1" value={rateLimit}
                      onChange={e => setRateLimit(e.target.value ? parseInt(e.target.value) : "")}
                      placeholder="e.g. 50"
                      className="glass-input w-full"
                    />
                  </div>
                  <div className="flex gap-3 pt-1">
                    <button type="button" onClick={() => setShowCreate(false)} className="btn-ghost flex-1 py-2.5 rounded-xl text-sm text-slate-300">Cancel</button>
                    <button type="submit" disabled={createQueue.isPending} className="btn-primary flex-1 py-2.5 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2">
                      {createQueue.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create Queue"}
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Queue"
        description={`Permanently delete "${deleteTarget?.name}"? All associated jobs will remain but no new jobs can be routed.`}
        confirmLabel="Delete Queue"
        variant="danger"
        isLoading={deleteQueue.isPending}
        onConfirm={() => { if (deleteTarget) { deleteQueue.mutate(deleteTarget.id); setDeleteTarget(null); } }}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
