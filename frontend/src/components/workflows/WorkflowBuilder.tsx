import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { X, Plus, Trash2, Save, Activity } from "lucide-react";
import { useOrgStore } from "../../store/useOrgStore";
import queuesService from "../../services/queues.service";
import { workflowsService, WorkflowNodeCreate } from "../../services/workflows.service";
import { toast } from "../../store/useNotification";

interface WorkflowBuilderProps {
  onClose: () => void;
  onSuccess: () => void;
}

export default function WorkflowBuilder({ onClose, onSuccess }: WorkflowBuilderProps) {
  const { activeOrgId, activeOrg } = useOrgStore();
  const [workflowName, setWorkflowName] = useState("");
  const [nodes, setNodes] = useState<WorkflowNodeCreate[]>([
    {
      temp_id: "node-1",
      name: "Step 1",
      queue_id: "",
      payload: {},
      dependencies: [],
      priority: 0,
      max_retries: 3,
    }
  ]);

  const { data: queues = [] } = useQuery({
    queryKey: ["queues", activeOrgId, activeOrg?.id],
    queryFn: () => queuesService.listQueues(activeOrgId!, activeOrg!.id),
    enabled: !!activeOrgId && !!activeOrg,
  });

  const mutation = useMutation({
    mutationFn: () => workflowsService.createWorkflow(activeOrgId!, activeOrg!.id, {
      name: workflowName,
      nodes,
    }),
    onSuccess: () => {
      toast.success("Workflow created successfully");
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create workflow");
    }
  });

  const addNode = () => {
    const prevNodeId = nodes[nodes.length - 1]?.temp_id;
    const newId = `node-${nodes.length + 1}`;
    setNodes([
      ...nodes,
      {
        temp_id: newId,
        name: `Step ${nodes.length + 1}`,
        queue_id: queues[0]?.id || "",
        payload: {},
        dependencies: prevNodeId ? [prevNodeId] : [], // Automatically chain it sequentially
        priority: 0,
        max_retries: 3,
      }
    ]);
  };

  const removeNode = (index: number) => {
    const newNodes = [...nodes];
    newNodes.splice(index, 1);
    
    // Fix broken dependencies
    newNodes.forEach((node, i) => {
      if (i > 0 && node.dependencies.length === 0) {
        node.dependencies = [newNodes[i - 1].temp_id];
      }
    });
    
    setNodes(newNodes);
  };

  const updateNode = (index: number, updates: Partial<WorkflowNodeCreate>) => {
    const newNodes = [...nodes];
    newNodes[index] = { ...newNodes[index], ...updates };
    setNodes(newNodes);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!workflowName) {
      toast.error("Workflow name is required");
      return;
    }
    if (nodes.some(n => !n.queue_id)) {
      toast.error("All steps must select a target queue");
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0f172a] rounded-2xl border border-white/10 shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between p-6 border-b border-white/5 bg-[#0a0f1c]">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            Build Workflow DAG
          </h2>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Workflow Name</label>
            <input
              type="text"
              value={workflowName}
              onChange={e => setWorkflowName(e.target.value)}
              placeholder="e.g. Data ETL Pipeline"
              className="w-full px-4 py-2.5 bg-[#0a0f1c] border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
              required
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-slate-300">Jobs Chain</h3>
              <button
                type="button"
                onClick={addNode}
                className="flex items-center gap-1.5 text-sm text-primary hover:text-primary/80 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Step
              </button>
            </div>
            
            <div className="space-y-4">
              {nodes.map((node, idx) => (
                <div key={node.temp_id} className="p-4 bg-white/[0.02] border border-white/5 rounded-xl relative group">
                  <div className="absolute -left-2.5 top-1/2 -translate-y-1/2 w-5 h-5 bg-[#0f172a] border border-white/10 rounded-full flex items-center justify-center text-[10px] text-slate-400 font-medium z-10">
                    {idx + 1}
                  </div>
                  
                  {idx > 0 && (
                    <div className="absolute top-0 left-0 w-px h-full bg-white/10 -ml-0.5 -mt-4"></div>
                  )}

                  <div className="ml-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Job Name</label>
                      <input
                        type="text"
                        value={node.name}
                        onChange={e => updateNode(idx, { name: e.target.value })}
                        className="w-full px-3 py-1.5 bg-[#0a0f1c] border border-white/10 rounded-lg text-sm text-white focus:border-primary/50 outline-none"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Target Queue</label>
                      <select
                        value={node.queue_id}
                        onChange={e => updateNode(idx, { queue_id: e.target.value })}
                        className="w-full px-3 py-1.5 bg-[#0a0f1c] border border-white/10 rounded-lg text-sm text-white focus:border-primary/50 outline-none"
                        required
                      >
                        <option value="" disabled>Select a queue</option>
                        {queues.map((q: any) => (
                          <option key={q.id} value={q.id}>{q.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  {nodes.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeNode(idx)}
                      className="absolute top-4 right-4 text-slate-500 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </form>

        <div className="p-6 border-t border-white/5 bg-[#0a0f1c] flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl font-medium text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={mutation.isPending}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary hover:bg-primary/90 text-white rounded-xl font-medium text-sm transition-all shadow-glow-primary disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {mutation.isPending ? "Saving..." : "Create Workflow"}
          </button>
        </div>
      </div>
    </div>
  );
}
