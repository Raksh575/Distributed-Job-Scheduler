import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ClipboardList, ShieldAlert, Calendar, Laptop, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import api from "../services/api";
import { useOrgStore } from "../store/useOrgStore";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";

interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  changes: Record<string, any> | null;
  ip_address: string | null;
  created_at: string;
}

export default function AuditLogs() {
  const { activeOrgId } = useOrgStore();
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  // 1. Fetch Audit Logs
  const { data: logs = [], isLoading } = useQuery<AuditLog[]>({
    queryKey: ["audit-logs", activeOrgId],
    queryFn: async () => {
      if (!activeOrgId) return [];
      const res = await api.get(`/organizations/${activeOrgId}/audit-logs`);
      return res.data;
    },
    enabled: !!activeOrgId,
  });

  const toggleExpand = (id: string) => {
    if (expandedLogId === id) {
      setExpandedLogId(null);
    } else {
      setExpandedLogId(id);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          <ClipboardList className="h-8 w-8 text-primary" />
          <span>Audit Log Trail</span>
        </h2>
        <p className="text-slate-400 mt-1">Review cluster actions, config revisions, and administrative logs for compliance.</p>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-10 w-10 text-primary animate-spin" />
          <span className="text-sm text-slate-500 mt-4">Loading audit trails...</span>
        </div>
      ) : logs.length === 0 ? (
        <div className="glass-panel p-16 text-center text-slate-500 rounded-2xl max-w-xl mx-auto space-y-4">
          <ShieldAlert className="h-12 w-12 text-slate-700 mx-auto" />
          <h3 className="text-lg font-bold text-white">No Audit Records</h3>
          <p className="text-xs text-slate-400">All administrative operations are quiet. No changes recorded yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {logs.map((log) => {
            const isExpanded = expandedLogId === log.id;
            return (
              <Card key={log.id} className="hover:border-slate-800 transition-colors duration-200">
                <CardContent className="pt-6 space-y-4">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    
                    <div className="space-y-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-bold text-white text-base">{log.action}</span>
                        <Badge variant="outline">{log.entity_type}</Badge>
                      </div>
                      
                      <div className="flex items-center gap-4 text-xs text-slate-400 pt-1 font-semibold">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5 text-slate-600" /> 
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                        {log.ip_address && (
                          <span className="flex items-center gap-1">
                            <Laptop className="h-3.5 w-3.5 text-slate-600" />
                            {log.ip_address}
                          </span>
                        )}
                        <span className="font-mono text-slate-500">Actor ID: {log.user_id?.substring(0, 8)}...</span>
                      </div>
                    </div>

                    {log.changes && (
                      <button
                        onClick={() => toggleExpand(log.id)}
                        className="text-xs text-primary hover:text-primary-light font-bold flex items-center gap-1 focus:outline-none shrink-0"
                      >
                        {isExpanded ? (
                          <>
                            Hide Diff <ChevronUp className="h-4 w-4" />
                          </>
                        ) : (
                          <>
                            Review Changes <ChevronDown className="h-4 w-4" />
                          </>
                        )}
                      </button>
                    )}

                  </div>

                  {isExpanded && log.changes && (
                    <div className="border-t border-slate-900 pt-4 mt-2">
                      <pre className="bg-slate-950/80 border border-slate-900 p-4 rounded-xl font-mono text-xs text-slate-300 overflow-x-auto">
                        {JSON.stringify(log.changes, null, 2)}
                      </pre>
                    </div>
                  )}

                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
