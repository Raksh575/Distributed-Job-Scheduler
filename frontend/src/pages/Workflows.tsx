import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import {
  GitBranch,
  Search,
  Plus,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronRight,
} from "lucide-react";
import { useOrgStore } from "../store/useOrgStore";
import { workflowsService } from "../services/workflows.service";
import WorkflowBuilder from "../components/workflows/WorkflowBuilder";
import { cn } from "../utils/cn";

export default function Workflows() {
  const navigate = useNavigate();
  const { activeOrgId, activeOrg } = useOrgStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);

  const { data: workflows = [], isLoading, refetch } = useQuery({
    queryKey: ["workflows", activeOrgId, activeOrg?.id],
    queryFn: () => workflowsService.listWorkflows(activeOrgId!, activeOrg!.id),
    enabled: !!activeOrgId && !!activeOrg,
    refetchInterval: 5000,
  });

  const filteredWorkflows = workflows.filter((w) =>
    w.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success": return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case "failed": return <XCircle className="w-4 h-4 text-rose-400" />;
      case "cancelled": return <AlertCircle className="w-4 h-4 text-slate-400" />;
      case "running": return <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />;
      default: return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case "success": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "failed": return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "cancelled": return "bg-slate-500/10 text-slate-400 border-slate-500/20";
      case "running": return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      default: return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 relative">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <GitBranch className="w-6 h-6 text-primary" />
              Workflows
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Design and monitor Directed Acyclic Graphs (DAGs) of dependent jobs.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search workflows..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-2 bg-[#0a0f1c] border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 w-full sm:w-64 transition-all"
              />
            </div>

            <button
              onClick={() => setIsBuilderOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-xl text-sm font-medium transition-all shadow-glow-primary"
            >
              <Plus className="w-4 h-4" />
              Create Workflow
            </button>
          </div>
        </div>

        {/* Workflows List */}
        <div className="space-y-4">
          {isLoading ? (
            <div className="flex justify-center p-12">
              <RefreshCw className="w-8 h-8 text-primary animate-spin" />
            </div>
          ) : filteredWorkflows.length === 0 ? (
            <div className="text-center p-12 bg-white/[0.02] border border-white/5 rounded-2xl">
              <GitBranch className="w-12 h-12 text-slate-500 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium text-white mb-2">No workflows found</h3>
              <p className="text-slate-400 text-sm mb-6 max-w-sm mx-auto">
                Create your first workflow to orchestrate complex dependencies across multiple queues.
              </p>
              <button
                onClick={() => setIsBuilderOpen(true)}
                className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary/10 text-primary border border-primary/20 rounded-xl hover:bg-primary/20 transition-colors font-medium text-sm"
              >
                <Plus className="w-4 h-4" />
                Build Workflow
              </button>
            </div>
          ) : (
            filteredWorkflows.map((workflow) => (
              <div
                key={workflow.id}
                onClick={() => navigate(`/workflows/${workflow.id}`)}
                className="group p-5 bg-white/[0.02] border border-white/5 rounded-2xl hover:bg-white/[0.04] hover:border-white/10 transition-all cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center border",
                      getStatusStyle(workflow.status)
                    )}>
                      {getStatusIcon(workflow.status)}
                    </div>
                    <div>
                      <h3 className="font-medium text-white group-hover:text-primary transition-colors">
                        {workflow.name}
                      </h3>
                      <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {format(new Date(workflow.created_at), "MMM d, yyyy HH:mm:ss")}
                        </span>
                        <span>•</span>
                        <span className="font-mono">{workflow.id}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className={cn(
                      "px-3 py-1 text-xs font-medium rounded-full border",
                      getStatusStyle(workflow.status)
                    )}>
                      {workflow.status.toUpperCase()}
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" />
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {isBuilderOpen && (
        <WorkflowBuilder
          onClose={() => setIsBuilderOpen(false)}
          onSuccess={() => {
            setIsBuilderOpen(false);
            refetch();
          }}
        />
      )}
    </div>
  );
}
