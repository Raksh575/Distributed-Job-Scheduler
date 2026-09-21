import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  MarkerType,
  Position,
  Handle,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  ArrowLeft,
  Play,
  XSquare,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Clock,
  Activity,
} from "lucide-react";

import { useOrgStore } from "../store/useOrgStore";
import { workflowsService } from "../services/workflows.service";
import { JobResponse } from "../services/jobs.service";
import { cn } from "../utils/cn";

// Custom Node Component to display Job status nicely
const JobNode = ({ data }: { data: any }) => {
  const { job } = data;
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success": return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case "failed": return <XCircle className="w-4 h-4 text-rose-400" />;
      case "cancelled": return <AlertCircle className="w-4 h-4 text-slate-400" />;
      case "queued":
      case "scheduled":
      case "running": return <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />;
      case "created":
      default: return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getBorderColor = (status: string) => {
    switch (status) {
      case "success": return "border-emerald-500/50 shadow-glow-emerald";
      case "failed": return "border-rose-500/50 shadow-glow-rose";
      case "cancelled": return "border-slate-500/50";
      case "queued":
      case "scheduled":
      case "running": return "border-blue-500/50 shadow-glow-primary";
      default: return "border-white/10";
    }
  };

  return (
    <div className={cn("px-4 py-3 bg-[#0a0f1c] rounded-xl border min-w-[200px]", getBorderColor(job.status))}>
      <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-slate-500" />
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-white truncate max-w-[140px]">{job.name}</h4>
        {getStatusIcon(job.status)}
      </div>
      <div className="flex justify-between items-center text-xs text-slate-400">
        <span className="capitalize">{job.status}</span>
        {job.progress > 0 && <span>{job.progress}%</span>}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-slate-500" />
    </div>
  );
};

const nodeTypes = {
  job: JobNode,
};

export default function WorkflowDetails() {
  const { workflowId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { activeOrgId } = useOrgStore();

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  const { data: workflow, isLoading, isError } = useQuery({
    queryKey: ["workflow", activeOrgId, workflowId],
    queryFn: () => workflowsService.getWorkflow(activeOrgId!, workflowId!),
    enabled: !!activeOrgId && !!workflowId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling if terminal status
      if (data && ["success", "failed", "cancelled"].includes(data.status)) return false;
      return 3000;
    }
  });

  const retryMutation = useMutation({
    mutationFn: () => workflowsService.retryWorkflow(activeOrgId!, workflowId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow", activeOrgId, workflowId] });
    }
  });

  const cancelMutation = useMutation({
    mutationFn: () => workflowsService.cancelWorkflow(activeOrgId!, workflowId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow", activeOrgId, workflowId] });
    }
  });

  // Build DAG whenever workflow jobs change
  useEffect(() => {
    if (!workflow || !workflow.jobs) return;
    
    // Very basic layout: group by levels using parent_id logic
    // This could be enhanced with a proper layout library like dagre, but we'll do a simple tier-based approach
    
    const nodeMap = new Map<string, Node>();
    const edgeList: Edge[] = [];
    
    // 1. Identify roots (no parent_id)
    const roots = workflow.jobs.filter(j => !j.parent_id);
    
    let currentLevel = roots;
    let y = 50;
    
    while (currentLevel.length > 0) {
      let x = 100;
      const nextLevel: JobResponse[] = [];
      
      currentLevel.forEach((job) => {
        nodeMap.set(job.id, {
          id: job.id,
          type: 'job',
          position: { x, y },
          data: { job },
        });
        
        x += 250; // spacing horizontally
        
        if (job.parent_id) {
          // Add edge from parent to this job
          edgeList.push({
            id: `e-${job.parent_id}-${job.id}`,
            source: job.parent_id,
            target: job.id,
            animated: ["running", "queued", "created"].includes(job.status),
            style: { stroke: job.status === "success" ? '#34d399' : '#64748b' },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: job.status === "success" ? '#34d399' : '#64748b',
            },
          });
        }
        
        // Find children
        const children = workflow.jobs!.filter(j => j.parent_id === job.id);
        nextLevel.push(...children);
      });
      
      currentLevel = nextLevel;
      y += 150; // vertical spacing
    }
    
    setNodes(Array.from(nodeMap.values()));
    setEdges(edgeList);
    
  }, [workflow]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Activity className="w-8 h-8 text-primary animate-pulse" />
      </div>
    );
  }

  if (isError || !workflow) {
    return (
      <div className="p-8 text-white">Error loading workflow.</div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#030712] relative overflow-hidden">
      {/* Header overlay */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-[#030712]/90 to-transparent p-6 pointer-events-none">
        <div className="max-w-6xl mx-auto flex items-center justify-between pointer-events-auto">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/workflows')}
              className="p-2 hover:bg-white/10 rounded-full transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-300" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-3">
                {workflow.name}
                <span className={cn(
                  "px-2.5 py-0.5 rounded-full text-xs font-medium border uppercase tracking-wider",
                  workflow.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  workflow.status === 'failed' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                  workflow.status === 'cancelled' ? 'bg-slate-500/10 text-slate-400 border-slate-500/20' :
                  'bg-blue-500/10 text-blue-400 border-blue-500/20'
                )}>
                  {workflow.status}
                </span>
              </h1>
              <p className="text-sm text-slate-400 mt-1 font-mono">
                {workflow.id} • Created {format(new Date(workflow.created_at), 'MMM d, yyyy HH:mm:ss')}
              </p>
            </div>
          </div>
          
          <div className="flex gap-3">
             {workflow.status === 'failed' && (
               <button
                 onClick={() => retryMutation.mutate()}
                 disabled={retryMutation.isPending}
                 className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-lg text-sm font-medium transition-colors"
               >
                 <Play className="w-4 h-4" />
                 Retry Failed
               </button>
             )}
             {["running"].includes(workflow.status) && (
               <button
                 onClick={() => cancelMutation.mutate()}
                 disabled={cancelMutation.isPending}
                 className="flex items-center gap-2 px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-sm font-medium transition-colors"
               >
                 <XSquare className="w-4 h-4" />
                 Cancel Workflow
               </button>
             )}
          </div>
        </div>
      </div>

      {/* Interactive DAG */}
      <div className="flex-1 w-full h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-right"
          className="bg-transparent"
        >
          <Background color="#334155" gap={20} size={1} />
          <Controls className="bg-[#0f172a] border-slate-700 fill-slate-300" />
        </ReactFlow>
      </div>
    </div>
  );
}
