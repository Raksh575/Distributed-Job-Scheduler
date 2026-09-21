import React from "react";
import { GlassCard } from "../shared/GlassCard";
import { cn } from "../../utils/cn";

export interface TimelineEvent {
  id: string;
  time: string;
  type: "info" | "warning" | "error" | "success";
  title: string;
  description: string;
}

export const ActivityTimeline = React.memo(({ title, events }: { title: string, events: TimelineEvent[] }) => {
  const getColor = (type: string) => {
    switch (type) {
      case "success": return "bg-emerald-500 border-emerald-500/30 text-emerald-400";
      case "warning": return "bg-amber-500 border-amber-500/30 text-amber-400";
      case "error":   return "bg-rose-500 border-rose-500/30 text-rose-400";
      case "info":
      default:        return "bg-blue-500 border-blue-500/30 text-blue-400";
    }
  };

  return (
    <GlassCard className="h-full overflow-hidden flex flex-col">
      <h3 className="text-sm font-bold text-white mb-4 tracking-wide shrink-0">{title}</h3>
      <div className="flex-1 overflow-y-auto pr-2 scrollbar-hide">
        <div className="relative border-l border-slate-700/50 ml-3 space-y-6 pb-4">
          {events.length === 0 ? (
            <p className="text-xs text-slate-500 pl-6">No recent activity.</p>
          ) : (
            events.map((event) => {
              const colorClasses = getColor(event.type);
              return (
                <div key={event.id} className="relative pl-6">
                  {/* Timeline dot */}
                  <div className={cn(
                    "absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full border-2 bg-slate-900",
                    colorClasses
                  )} />
                  
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className={cn("text-xs font-semibold uppercase tracking-wider", colorClasses.split(" ")[2])}>
                        {event.title}
                      </span>
                      <span className="text-[10px] text-slate-500">{event.time}</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {event.description}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </GlassCard>
  );
});
ActivityTimeline.displayName = "ActivityTimeline";
