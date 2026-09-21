import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  useReactTable, getCoreRowModel, getSortedRowModel,
  getFilteredRowModel,
  ColumnDef, SortingState, flexRender
} from "@tanstack/react-table";
import {
  Activity, Plus, Search, ChevronDown, ChevronUp,
  ChevronLeft, ChevronRight, X, ExternalLink,
  RotateCcw, Ban, Loader2, RefreshCcw
} from "lucide-react";
import { useOrgStore } from "../store/useOrgStore";
import { useJobs, useSubmitJob, useCancelJob, useReplayJob } from "../hooks/useJobs";
import { useQueues } from "../hooks/useQueues";
import { JobResponse } from "../services/jobs.service";
import orgsService from "../services/orgs.service";
import { StatusBadge } from "../components/shared/StatusBadge";
import { GlassCard } from "../components/shared/GlassCard";
import { PageHeader } from "../components/shared/PageHeader";
import { EmptyState } from "../components/shared/EmptyState";
import { SkeletonTable } from "../components/shared/SkeletonCard";
import { ConfirmDialog } from "../components/shared/ConfirmDialog";
import { cn } from "../utils/cn";
import { extractApiError } from "../services/api";

const STATUS_FILTERS = ["all", "queued", "running", "success", "failed", "cancelled"] as const;

function formatRelativeTime(date: string) {
  const diff = Date.now() - new Date(date).getTime();
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return new Date(date).toLocaleDateString();
}

export default function Jobs() {
  const navigate = useNavigate();
  const { activeOrgId } = useOrgStore();

  const queryClient = useQueryClient();

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
      await queryClient.invalidateQueries({ queryKey: ["projects", activeOrgId] });
      await refetchProjects();
    } finally {
      setProvisioningProject(false);
    }
  };
  const { data: queues = [] } = useQueues(activeOrgId, projectId);

  const [selectedQueue, setSelectedQueue] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [globalFilter, setGlobalFilter] = useState("");
  const [sorting, setSorting] = useState<SortingState>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [cancelTarget, setCancelTarget] = useState<JobResponse | null>(null);
  const [page, setPage] = useState(0);

  // Pick first queue by default
  const queueId = selectedQueue || queues[0]?.id || null;

  const { data: jobs = [], isLoading, isError } = useJobs(activeOrgId, queueId, page * 50, 50);
  const cancelJob = useCancelJob(activeOrgId!);
  const replayJob = useReplayJob(activeOrgId!);

  const filteredJobs = useMemo(() =>
    statusFilter === "all" ? jobs : jobs.filter(j => j.status === statusFilter),
    [jobs, statusFilter]
  );

  const columns: ColumnDef<JobResponse>[] = useMemo(() => [
    {
      accessorKey: "name",
      header: "Job Name",
      cell: ({ row }) => (
        <button
          onClick={() => navigate(`/jobs/${row.original.id}`)}
          className="text-white font-semibold hover:text-blue-400 transition-colors flex items-center gap-1.5 text-left"
        >
          {row.original.name}
          <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100" />
        </button>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <StatusBadge status={row.original.status as any} pulse size="sm" />,
    },
    {
      accessorKey: "priority",
      header: "Priority",
      cell: ({ row }) => (
        <span className="font-mono text-xs text-slate-400">{row.original.priority}</span>
      ),
    },
    {
      accessorKey: "retries_count",
      header: "Retries",
      cell: ({ row }) => (
        <span className="font-mono text-xs text-slate-400">
          {row.original.retries_count} / {row.original.max_retries}
        </span>
      ),
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => (
        <span className="text-xs text-slate-400 font-mono">
          {formatRelativeTime(row.original.created_at)}
        </span>
      ),
    },
    {
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <div className="flex items-center gap-1 justify-end">
          {(row.original.status === "failed" || row.original.status === "cancelled") && (
            <button
              onClick={() => replayJob.mutate(row.original.id)}
              disabled={replayJob.isPending}
              className="p-1.5 text-slate-500 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-all"
              title="Replay"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          )}
          {(row.original.status === "queued" || row.original.status === "running") && (
            <button
              onClick={() => setCancelTarget(row.original)}
              className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
              title="Cancel"
            >
              <Ban className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      ),
    },
  ], [navigate, replayJob, cancelJob]);

  const table = useReactTable({
    data: filteredJobs,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Jobs"
        subtitle="Manage and monitor background job executions"
        icon={Activity}
        actions={
          <button
            onClick={() => setShowCreateModal(true)}
            disabled={!queueId}
            className="btn-primary px-4 py-2.5 rounded-xl text-sm font-semibold text-white flex items-center gap-2 disabled:opacity-50"
          >
            <Plus className="h-4 w-4" /> Submit Job
          </button>
        }
      />

      <GlassCard padding="none">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 p-4 border-b border-white/5">
          {/* Queue selector */}
          <select
            value={selectedQueue}
            onChange={(e) => { setSelectedQueue(e.target.value); setPage(0); }}
            className="glass-input py-2 text-xs min-w-[180px]"
          >
            {queues.map(q => (
              <option key={q.id} value={q.id} className="bg-[#0a1020]">{q.name}</option>
            ))}
            {queues.length === 0 && <option value="">No queues</option>}
          </select>

          {/* Status filters */}
          <div className="flex gap-1">
            {STATUS_FILTERS.map(s => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={cn(
                  "px-2.5 py-1 rounded-lg text-xs font-medium transition-all capitalize",
                  statusFilter === s
                    ? "bg-blue-600/20 text-blue-300 border border-blue-500/25"
                    : "text-slate-500 hover:text-slate-300 hover:bg-white/5"
                )}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative ml-auto">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
            <input
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              placeholder="Search jobs…"
              className="glass-input pl-9 py-2 text-xs w-48"
            />
          </div>
        </div>

        {/* Table */}
        {isLoading || projectsLoading ? (
          <SkeletonTable rows={8} />
        ) : isError ? (
          <div className="p-8 text-center text-slate-500 text-sm">Failed to load jobs. Check queue selection.</div>
        ) : !projectId ? (
          <EmptyState
            icon={Activity}
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
        ) : filteredJobs.length === 0 ? (
          <EmptyState icon={Activity} title="No jobs found" description="Submit a job to this queue to get started." />
        ) : (
          <div className="overflow-x-auto">
            <table className="premium-table">
              <thead>
                {table.getHeaderGroups().map(hg => (
                  <tr key={hg.id}>
                    {hg.headers.map(header => (
                      <th
                        key={header.id}
                        className={cn("cursor-pointer select-none", header.column.getCanSort() && "hover:text-white transition-colors")}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        <div className="flex items-center gap-1">
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {header.column.getIsSorted() === "asc" && <ChevronUp className="h-3 w-3" />}
                          {header.column.getIsSorted() === "desc" && <ChevronDown className="h-3 w-3" />}
                        </div>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map(row => (
                  <tr key={row.id} className="group cursor-pointer" onClick={() => navigate(`/jobs/${row.original.id}`)}>
                    {row.getVisibleCells().map(cell => (
                      <td key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!isLoading && filteredJobs.length > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-white/5">
            <p className="text-xs text-slate-500">{filteredJobs.length} jobs</p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="btn-ghost p-1.5 rounded-lg text-slate-400 disabled:opacity-30"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-xs text-slate-400 px-2 py-1">Page {page + 1}</span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={jobs.length < 50}
                className="btn-ghost p-1.5 rounded-lg text-slate-400 disabled:opacity-30"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </GlassCard>

      {/* Submit Job Modal */}
      <SubmitJobModal
        open={showCreateModal}
        queues={queues}
        defaultQueueId={queueId ?? ""}
        orgId={activeOrgId!}
        onClose={() => setShowCreateModal(false)}
      />

      {/* Cancel Confirm */}
      <ConfirmDialog
        open={!!cancelTarget}
        title="Cancel Job"
        description={`Cancel job "${cancelTarget?.name}"? This cannot be undone.`}
        confirmLabel="Cancel Job"
        variant="danger"
        isLoading={cancelJob.isPending}
        onConfirm={() => { if (cancelTarget) { cancelJob.mutate(cancelTarget.id); setCancelTarget(null); } }}
        onCancel={() => setCancelTarget(null)}
      />
    </div>
  );
}

function SubmitJobModal({ open, queues, defaultQueueId, orgId, onClose }: {
  open: boolean;
  queues: any[];
  defaultQueueId: string;
  orgId: string;
  onClose: () => void;
}) {
  const [name, setName] = useState("");
  const [queueId, setQueueId] = useState(defaultQueueId);
  const [payloadStr, setPayloadStr] = useState("{}");
  const [priority, setPriority] = useState(0);
  const [maxRetries, setMaxRetries] = useState(3);
  const [delay, setDelay] = useState<number | "">("");
  const [timeout, setTimeoutVal] = useState<number | "">("");
  const [payloadError, setPayloadError] = useState("");
  const [submitError, setSubmitError] = useState("");

  const submitJob = useSubmitJob(orgId, queueId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPayloadError("");
    setSubmitError("");
    let payload: Record<string, unknown> = {};
    try { payload = JSON.parse(payloadStr); } catch { setPayloadError("Invalid JSON payload"); return; }
    try {
      await submitJob.mutateAsync({
        name,
        payload,
        priority,
        max_retries: maxRetries,
        delay_seconds: delay !== "" && Number(delay) > 0 ? Number(delay) : undefined,
        timeout: timeout !== "" && Number(timeout) > 0 ? Number(timeout) : undefined,
      });
      setName(""); setPayloadStr("{}"); onClose();
    } catch (err: unknown) {
      setSubmitError(extractApiError(err));
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose} className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]" />
          <motion.div initial={{ opacity: 0, scale: 0.93 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.93 }}
            transition={{ type: "spring", stiffness: 350, damping: 28 }}
            className="fixed inset-0 z-[101] flex items-center justify-center p-4">
            <div className="glass-card gradient-border rounded-2xl p-6 w-full max-w-lg">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-base font-bold text-white">Submit New Job</h3>
                <button onClick={onClose} className="text-slate-500 hover:text-white"><X className="h-4 w-4" /></button>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">Job Name</label>
                  <input type="text" required value={name} onChange={e => setName(e.target.value)} placeholder="process-report" className="glass-input w-full font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">Target Queue</label>
                  <select value={queueId} onChange={e => setQueueId(e.target.value)} className="glass-input w-full">
                    {queues.map(q => <option key={q.id} value={q.id} className="bg-[#0a1020]">{q.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">Payload (JSON)</label>
                  <textarea
                    value={payloadStr} onChange={e => setPayloadStr(e.target.value)}
                    rows={4} className="glass-input w-full font-mono text-xs resize-none"
                    placeholder='{"key": "value"}'
                  />
                  {payloadError && <p className="text-xs text-red-400 mt-1">{payloadError}</p>}
                  {submitError && <p className="text-xs text-red-400 mt-1">{submitError}</p>}
                </div>
                <div className="grid grid-cols-4 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Priority</label>
                    <input type="number" min={0} max={1000} value={priority} onChange={e => setPriority(+e.target.value)} className="glass-input w-full font-mono" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Max Retries</label>
                    <input type="number" min={0} max={20} value={maxRetries} onChange={e => setMaxRetries(+e.target.value)} className="glass-input w-full font-mono" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Delay (s)</label>
                    <input type="number" min={0} value={delay} onChange={e => setDelay(e.target.value ? parseInt(e.target.value) : "")} placeholder="0" className="glass-input w-full font-mono" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5">Timeout (s)</label>
                    <input type="number" min={0} value={timeout} onChange={e => setTimeoutVal(e.target.value ? parseInt(e.target.value) : "")} placeholder="none" className="glass-input w-full font-mono" />
                  </div>
                </div>
                <div className="flex gap-3 pt-1">
                  <button type="button" onClick={onClose} className="btn-ghost flex-1 py-2.5 rounded-xl text-sm font-medium text-slate-300">Cancel</button>
                  <button type="submit" disabled={submitJob.isPending || !queueId} className="btn-primary flex-1 py-2.5 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-50">
                    {submitJob.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Submit Job"}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
