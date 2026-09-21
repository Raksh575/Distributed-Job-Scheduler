import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  Play, 
  Square, 
  Loader2,
  Sliders,
  Sparkles
} from "lucide-react";
import api from "../services/api";
import { useOrgStore } from "../store/useOrgStore";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";

export default function Simulator() {
  const { activeOrgId } = useOrgStore();
  const queryClient = useQueryClient();
  const [jobCount, setJobCount] = useState(100);
  const [isSimulating, setIsSimulating] = useState(false);

  // Observability metrics query to show active scaling counts
  const { data: metrics } = useQuery({
    queryKey: ["observability-metrics", activeOrgId],
    queryFn: async () => {
      const res = await api.get(`/organizations/${activeOrgId}/observability/metrics`);
      return res.data;
    },
    refetchInterval: isSimulating ? 1000 : 5000,
    enabled: !!activeOrgId
  });

  const triggerMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/organizations/${activeOrgId}/simulator/trigger`, null, {
        params: { job_count: jobCount }
      });
      return res.data;
    },
    onSuccess: () => {
      setIsSimulating(true);
      queryClient.invalidateQueries({ queryKey: ["observability-metrics"] });
    }
  });

  const stopMutation = useMutation({
    mutationFn: async () => {
      const qId = metrics?.queue_analytics?.[0]?.queue_id;
      if (qId) {
        await api.post(`/organizations/${activeOrgId}/simulator/stop`, null, {
          params: { queue_id: qId }
        });
      }
    },
    onSuccess: () => {
      setIsSimulating(false);
      queryClient.invalidateQueries({ queryKey: ["observability-metrics"] });
    }
  });

  const sys = metrics?.system_metrics;
  const queues = metrics?.queue_analytics || [];

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Sliders className="h-8 w-8 text-primary" />
            <span>Load & Scaling Cockpit</span>
          </h2>
          <p className="text-slate-400 mt-1">Stress test queue engines and auto-scale cluster nodes dynamically.</p>
        </div>
        <Badge variant={isSimulating ? "default" : "secondary"} className="h-7 text-xs font-semibold px-4.5 rounded-lg shrink-0 self-start md:self-center">
          {isSimulating ? "Simulation Active" : "Simulator Idle"}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Panel: Trigger Cockpit Controls */}
        <div className="space-y-6 lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Controls Console</CardTitle>
              <CardDescription>Configure stress workload parameters.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Job Count Selector */}
              <div className="space-y-3">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block">Workload Volume</label>
                <div className="grid grid-cols-3 gap-2">
                  {[100, 1000, 10000].map((count) => (
                    <button
                      key={count}
                      onClick={() => setJobCount(count)}
                      disabled={isSimulating}
                      className={`py-3 rounded-xl border font-bold transition-all text-sm ${
                        jobCount === count
                          ? "bg-primary border-primary text-white shadow-glow-blue"
                          : "bg-slate-950/40 border-slate-800 text-slate-400 hover:text-white disabled:opacity-50"
                      }`}
                    >
                      {count} Jobs
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Triggers */}
              <div className="space-y-3 pt-4 border-t border-slate-900">
                {!isSimulating ? (
                  <Button
                    onClick={() => triggerMutation.mutate()}
                    disabled={triggerMutation.isPending}
                    className="w-full h-12 text-sm font-bold flex items-center justify-center gap-2"
                  >
                    {triggerMutation.isPending ? (
                      <Loader2 className="h-4.5 w-4.5 animate-spin" />
                    ) : (
                      <>
                        <Play className="h-4.5 w-4.5 fill-current" /> Inject Load Workload
                      </>
                    )}
                  </Button>
                ) : (
                  <Button
                    onClick={() => stopMutation.mutate()}
                    disabled={stopMutation.isPending}
                    variant="destructive"
                    className="w-full h-12 text-sm font-bold flex items-center justify-center gap-2"
                  >
                    {stopMutation.isPending ? (
                      <Loader2 className="h-4.5 w-4.5 animate-spin" />
                    ) : (
                      <>
                        <Square className="h-4.5 w-4.5 fill-current" /> Terminate Load
                      </>
                    )}
                  </Button>
                )}
              </div>

            </CardContent>
          </Card>

          {/* AI Helper Banner */}
          <Card className="bg-gradient-to-tr from-slate-950 to-primary/10 border-primary/20">
            <CardContent className="pt-6 space-y-3">
              <h4 className="font-bold text-white text-sm flex items-center gap-1.5">
                <Sparkles className="h-4.5 w-4.5 text-primary animate-pulse" />
                <span>Simulation Insights</span>
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                When stressed with loads exceeding 50 jobs, the system automatically registers mock scale workers in the DB, distributing processing loads. Demobilized workers scale-in once queues clear.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Right Panel: Auto Scaling Graphs */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Status Dials */}
          {sys && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <Card className="p-5 flex flex-col justify-between h-32">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Active Workers</span>
                <p className="text-3xl font-extrabold text-white mt-2 flex items-baseline gap-2">
                  <span>{sys.active_workers}</span>
                  <span className="text-xs text-slate-500 font-medium font-sans">Nodes online</span>
                </p>
              </Card>

              <Card className="p-5 flex flex-col justify-between h-32">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Queue Backlog</span>
                <p className="text-3xl font-extrabold text-white mt-2 flex items-baseline gap-2">
                  <span>{sys.waiting_jobs}</span>
                  <span className="text-xs text-slate-500 font-medium font-sans">Waiting tasks</span>
                </p>
              </Card>

              <Card className="p-5 flex flex-col justify-between h-32">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">System CPU Load</span>
                <p className="text-3xl font-extrabold text-white mt-2 flex items-baseline gap-2">
                  <span>{sys.cpu_usage}%</span>
                  <span className="text-xs text-slate-500 font-medium font-sans">Host load</span>
                </p>
              </Card>
            </div>
          )}

          {/* Queue telemetries details */}
          <Card>
            <CardHeader>
              <CardTitle>Queue Throughput Diagnostics</CardTitle>
              <CardDescription>Live backlog queues load length and execution timings.</CardDescription>
            </CardHeader>
            <CardContent>
              {queues.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">No queue telemetry available.</p>
              ) : (
                <div className="space-y-4">
                  {queues.map((q: any) => (
                    <div key={q.queue_id} className="space-y-2">
                      <div className="flex justify-between text-xs text-slate-300 font-semibold">
                        <span>{q.queue_name} backlog load</span>
                        <span>{q.queue_size} pending</span>
                      </div>
                      <div className="w-full bg-slate-900 border border-slate-800 rounded-full h-3">
                        {/* Progress width capped to represent backlog scale */}
                        <div 
                          className="bg-gradient-to-r from-primary to-primary-light h-3 rounded-full transition-all duration-500" 
                          style={{ width: `${Math.min(100, (q.queue_size / 200) * 100)}%` }} 
                        />
                      </div>
                      <div className="flex justify-between text-[10px] text-slate-500 pt-1">
                        <span>Avg execution time: {q.avg_execution_ms}ms</span>
                        <span>Avg wait latency: {q.avg_wait_seconds}s</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

        </div>

      </div>
    </div>
  );
}
