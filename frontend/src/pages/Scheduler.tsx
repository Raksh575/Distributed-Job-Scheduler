import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, ToggleLeft, ToggleRight, Trash2, Clock, Loader2 } from "lucide-react";
import { useOrgStore } from "../store/useOrgStore";
import orgsService from "../services/orgs.service";
import queuesService from "../services/queues.service";
import schedulesService from "../services/schedules.service";
import { toast } from "../store/useNotification";
import { GlassCard } from "../components/shared/GlassCard";

export default function Scheduler() {
  const { activeOrgId } = useOrgStore();
  const queryClient = useQueryClient();

  // Form states
  const [taskName, setTaskName] = useState("");
  const [triggerMode, setTriggerMode] = useState<"cron" | "interval">("cron");
  const [cronExpression, setCronExpression] = useState("*/10 * * * *");
  const [intervalSeconds, setIntervalSeconds] = useState(600);
  const [selectedQueueId, setSelectedQueueId] = useState("");
  const [jobName, setJobName] = useState("send_email");
  const [jobPayload, setJobPayload] = useState("{}");

  // 1. Fetch Projects of active organization
  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ["projects", activeOrgId],
    queryFn: () => orgsService.listProjects(activeOrgId!),
    enabled: !!activeOrgId,
  });

  const projectId = projects[0]?.id ?? null;

  // 2. Fetch Queues of default project
  const { data: queues = [], isLoading: queuesLoading } = useQuery({
    queryKey: ["queues", activeOrgId, projectId],
    queryFn: () => queuesService.listQueues(activeOrgId!, projectId!),
    enabled: !!activeOrgId && !!projectId,
  });

  // 3. Fetch Schedules
  const { data: schedules = [], isLoading: schedulesLoading } = useQuery({
    queryKey: ["schedules", activeOrgId, projectId],
    queryFn: () => schedulesService.listSchedules(activeOrgId!, projectId!),
    enabled: !!activeOrgId && !!projectId,
  });

  // Actions
  const createMutation = useMutation({
    mutationFn: (payload: any) => schedulesService.createSchedule(activeOrgId!, projectId!, payload),
    onSuccess: () => {
      toast.success("Schedule created successfully");
      queryClient.invalidateQueries({ queryKey: ["schedules", activeOrgId, projectId] });
      setTaskName("");
    },
    onError: (err: any) => {
      toast.error("Failed to create schedule", err.response?.data?.error?.message || err.message);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => schedulesService.deleteSchedule(activeOrgId!, id),
    onSuccess: () => {
      toast.success("Schedule deleted");
      queryClient.invalidateQueries({ queryKey: ["schedules", activeOrgId, projectId] });
    },
    onError: (err: any) => {
      toast.error("Delete failed", err.response?.data?.error?.message || err.message);
    }
  });

  const pauseMutation = useMutation({
    mutationFn: (id: string) => schedulesService.pauseSchedule(activeOrgId!, id),
    onSuccess: () => {
      toast.success("Schedule paused");
      queryClient.invalidateQueries({ queryKey: ["schedules", activeOrgId, projectId] });
    },
    onError: (err: any) => {
      toast.error("Pause failed", err.response?.data?.error?.message || err.message);
    }
  });

  const resumeMutation = useMutation({
    mutationFn: (id: string) => schedulesService.resumeSchedule(activeOrgId!, id),
    onSuccess: () => {
      toast.success("Schedule resumed");
      queryClient.invalidateQueries({ queryKey: ["schedules", activeOrgId, projectId] });
    },
    onError: (err: any) => {
      toast.error("Resume failed", err.response?.data?.error?.message || err.message);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskName) {
      toast.error("Task name is required");
      return;
    }
    if (!selectedQueueId && queues.length > 0) {
      toast.error("Please select a target queue");
      return;
    }

    let parsedPayload = {};
    try {
      parsedPayload = JSON.parse(jobPayload);
    } catch (err) {
      toast.error("Invalid JSON payload structure");
      return;
    }

    const payload: any = {
      name: taskName,
      trigger_type: triggerMode,
      target_queue_id: selectedQueueId || queues[0]?.id,
      job_name: jobName,
      job_payload: parsedPayload,
    };

    if (triggerMode === "cron") {
      payload.cron_expression = cronExpression;
    } else {
      payload.interval_seconds = Number(intervalSeconds);
    }

    createMutation.mutate(payload);
  };

  const isLoading = projectsLoading || queuesLoading || schedulesLoading;

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Schedules</h2>
          <p className="text-slate-400 mt-1">Configure and manage cron expressions and repeating task interval parameters.</p>
        </div>
      </div>

      {/* Grid structure */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Form: Create New Schedule */}
        <GlassCard className="h-fit">
          <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
            <CalendarDays className="h-5 w-5 text-primary" />
            <span>Create Scheduled Task</span>
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Task Name</label>
              <input 
                type="text" 
                required
                value={taskName}
                onChange={e => setTaskName(e.target.value)}
                placeholder="e.g. database_cleanup" 
                className="glass-input w-full" 
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Trigger Mode</label>
              <select 
                value={triggerMode}
                onChange={e => setTriggerMode(e.target.value as any)}
                className="glass-input w-full bg-[#0a1020]"
              >
                <option value="cron">Cron Expression</option>
                <option value="interval">Repeat Interval (Seconds)</option>
              </select>
            </div>

            {triggerMode === "cron" ? (
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Cron String</label>
                <input 
                  type="text" 
                  required
                  value={cronExpression}
                  onChange={e => setCronExpression(e.target.value)}
                  placeholder="e.g. */10 * * * *" 
                  className="glass-input w-full font-mono" 
                />
              </div>
            ) : (
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Interval (Seconds)</label>
                <input 
                  type="number" 
                  required
                  value={intervalSeconds}
                  onChange={e => setIntervalSeconds(Number(e.target.value))}
                  placeholder="e.g. 600" 
                  className="glass-input w-full font-mono" 
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Target Queue</label>
              <select
                value={selectedQueueId}
                onChange={e => setSelectedQueueId(e.target.value)}
                className="glass-input w-full bg-[#0a1020]"
              >
                <option value="" disabled>Select a Queue</option>
                {queues.map(q => (
                  <option key={q.id} value={q.id}>{q.name}</option>
                ))}
                {queues.length === 0 && <option value="" disabled>No queues available</option>}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Job Type / Name</label>
              <input 
                type="text" 
                required
                value={jobName}
                onChange={e => setJobName(e.target.value)}
                placeholder="e.g. send_email" 
                className="glass-input w-full" 
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Job Payload (JSON)</label>
              <textarea 
                value={jobPayload}
                onChange={e => setJobPayload(e.target.value)}
                rows={3}
                placeholder="{}" 
                className="glass-input w-full font-mono text-xs" 
              />
            </div>

            <button 
              type="submit"
              disabled={createMutation.isPending || isLoading}
              className="w-full h-11 bg-primary hover:bg-primary/80 rounded-xl text-white font-semibold transition-all shadow-glow-primary mt-2 flex items-center justify-center gap-2"
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Schedule Task"}
            </button>
          </form>
        </GlassCard>

        {/* Right Listing: Active Schedules */}
        <div className="lg:col-span-2 space-y-4">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
              <span className="text-sm text-slate-500 mt-2">Loading schedules...</span>
            </div>
          ) : schedules.length === 0 ? (
            <div className="glass-panel p-10 text-center text-slate-500 rounded-2xl">
              No schedules registered. Complete the form to create your first scheduled task.
            </div>
          ) : (
            schedules.map((sched) => (
              <GlassCard key={sched.id} className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-3">
                    <h4 className="text-base font-bold text-white">{sched.name}</h4>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${
                      sched.trigger_type === "cron" ? "bg-blue-500/10 text-blue-400 border border-blue-500/10" : "bg-purple-500/10 text-purple-400 border border-purple-500/10"
                    }`}>
                      {sched.trigger_type}
                    </span>
                  </div>
                  
                  <p className="text-xs text-slate-400">
                    Parameter: <span className="font-mono text-white bg-slate-900 border border-white/5 px-1.5 py-0.5 rounded">{sched.cron_expression || `${sched.interval_seconds}s`}</span>
                  </p>

                  <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5" />
                      Next fire: {sched.next_run_time ? new Date(sched.next_run_time).toLocaleString() : "Suspended"}
                    </span>
                    <span>Job: <span className="font-mono text-slate-300">{sched.job_name}</span></span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-3 self-end md:self-auto border-t md:border-t-0 border-slate-800/60 pt-4 md:pt-0">
                  {/* Active Toggle */}
                  <button 
                    onClick={() => {
                      if (sched.is_active) pauseMutation.mutate(sched.id);
                      else resumeMutation.mutate(sched.id);
                    }} 
                    disabled={pauseMutation.isPending || resumeMutation.isPending}
                    className="text-slate-400 hover:text-white transition-colors"
                    title={sched.is_active ? "Pause schedule" : "Activate schedule"}
                  >
                    {sched.is_active ? (
                      <ToggleRight className="h-9 w-9 text-primary" />
                    ) : (
                      <ToggleLeft className="h-9 w-9 text-slate-600" />
                    )}
                  </button>

                  {/* Delete */}
                  <button 
                    onClick={() => deleteMutation.mutate(sched.id)} 
                    disabled={deleteMutation.isPending}
                    className="p-2 bg-red-950/20 hover:bg-red-950/30 border border-red-900/30 rounded-xl text-red-400 hover:text-red-300 transition-all"
                    title="Remove schedule"
                  >
                    <Trash2 className="h-4.5 w-4.5" />
                  </button>
                </div>
              </GlassCard>
            ))
          )}
        </div>

      </div>
    </div>
  );
}
