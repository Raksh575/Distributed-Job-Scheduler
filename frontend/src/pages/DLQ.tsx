import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Shield, RotateCcw, Trash2, Search, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { useOrgStore } from "../store/useOrgStore";
import dlqService from "../services/dlq.service";
import { toast } from "../store/useNotification";
import { GlassCard } from "../components/shared/GlassCard";
import { PageHeader } from "../components/shared/PageHeader";
import { EmptyState } from "../components/shared/EmptyState";
import { SkeletonTable } from "../components/shared/SkeletonCard";
import { ConfirmDialog } from "../components/shared/ConfirmDialog";

function useDLQ(orgId: string | null, skip: number, limit: number) {
  return useQuery({
    queryKey: ["dlq", orgId, skip, limit],
    queryFn: () => dlqService.listDLQ(orgId!, skip, limit),
    enabled: !!orgId,
    refetchInterval: 15000,
  });
}

export default function DLQ() {
  const { activeOrgId } = useOrgStore();
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const { data: records = [], isLoading, isError } = useDLQ(activeOrgId, page * 50, 50);

  const replayMutation = useMutation({
    mutationFn: (jobId: string) => dlqService.replayJob(activeOrgId!, jobId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dlq", activeOrgId] });
      toast.success("Job replayed", `Job has been re-queued.`);
    },
    onError: (err: any) => toast.error("Replay failed", err.response?.data?.error?.message || err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => dlqService.deleteJob(activeOrgId!, jobId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dlq", activeOrgId] });
      toast.success("Record deleted");
      setDeleteTarget(null);
    },
    onError: (err: any) => toast.error("Delete failed", err.response?.data?.error?.message || err.message),
  });

  const filteredRecords = search
    ? records.filter(r => r.job_id.includes(search) || r.reason?.toLowerCase().includes(search.toLowerCase()))
    : records;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dead Letter Queue"
        subtitle="Failed jobs that exceeded retry limits"
        icon={Shield}
        actions={
          <div className="text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20 px-2.5 py-1 rounded-lg">
            {records.length} records
          </div>
        }
      />

      <GlassCard padding="none">
        {/* Search */}
        <div className="p-4 border-b border-white/5 flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
            <input
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search by job ID or reason…"
              className="glass-input pl-9 py-2 text-xs w-full"
            />
          </div>
        </div>

        {isLoading ? (
          <SkeletonTable rows={6} />
        ) : isError ? (
          <div className="p-8 text-center text-slate-500 text-sm">Failed to load DLQ records.</div>
        ) : filteredRecords.length === 0 ? (
          <EmptyState
            icon={Shield}
            title="Dead Letter Queue is empty"
            description="All jobs are processing normally. No failures requiring manual review."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="premium-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>AI Analysis</th>
                  <th>Failed At</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((record, i) => (
                  <motion.tr
                    key={record.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.02 }}
                    className="group"
                  >
                    <td>
                      <span className="font-mono text-xs text-slate-300">{record.job_id.slice(0, 20)}…</span>
                    </td>
                    <td>
                      {(() => {
                        try {
                          const parsed = JSON.parse(record.reason);
                          if (parsed.analysis) {
                            return (
                              <div className="flex flex-col gap-1">
                                <span className="text-[10px] uppercase font-bold text-slate-500">{parsed.analysis.error_category}</span>
                                <span className="text-xs text-red-300/80 max-w-xs truncate block">{parsed.analysis.failure_summary}</span>
                              </div>
                            );
                          }
                          return <span className="text-xs text-red-300/80 max-w-xs truncate block">{parsed.message || record.reason}</span>;
                        } catch (e) {
                          return <span className="text-xs text-red-300/80 max-w-xs truncate block">{record.reason || "Unknown"}</span>;
                        }
                      })()}
                    </td>
                    <td>
                      <span className="text-xs text-slate-400 font-mono">
                        {new Date(record.failed_at).toLocaleString()}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-1 justify-end">
                        <button
                          onClick={() => replayMutation.mutate(record.job_id)}
                          disabled={replayMutation.isPending}
                          className="p-1.5 text-slate-500 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-all"
                          title="Replay"
                        >
                          {replayMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RotateCcw className="h-3.5 w-3.5" />}
                        </button>
                        <button
                          onClick={() => setDeleteTarget(record.job_id)}
                          className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                          title="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!isLoading && filteredRecords.length > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-white/5">
            <p className="text-xs text-slate-500">{filteredRecords.length} records</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="btn-ghost p-1.5 rounded-lg text-slate-400 disabled:opacity-30">
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-xs text-slate-400 px-2 py-1">Page {page + 1}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={records.length < 50} className="btn-ghost p-1.5 rounded-lg text-slate-400 disabled:opacity-30">
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </GlassCard>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete DLQ Record"
        description="Permanently remove this record from the dead letter queue? The original job data will be lost."
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
        onConfirm={() => { if (deleteTarget) deleteMutation.mutate(deleteTarget); }}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
