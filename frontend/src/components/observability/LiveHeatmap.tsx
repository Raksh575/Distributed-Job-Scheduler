import React from "react";
import { GlassCard } from "../shared/GlassCard";

interface HeatmapNode {
  id: string;
  name: string;
  value: number; // 0 to 1
  status: "success" | "warning" | "error" | "offline";
}

export const LiveHeatmap = React.memo(({ title, nodes }: { title: string, nodes: HeatmapNode[] }) => {
  const getStatusColor = (status: string, value: number) => {
    // Opacity based on value (0-1)
    const opacity = Math.max(0.2, value);
    switch (status) {
      case "success": return `rgba(52, 211, 153, ${opacity})`; // emerald
      case "warning": return `rgba(251, 191, 36, ${opacity})`; // amber
      case "error":   return `rgba(244, 63, 94, ${opacity})`;  // rose
      case "offline": return `rgba(100, 116, 139, 0.2)`;       // slate
      default:        return `rgba(59, 130, 246, ${opacity})`; // blue
    }
  };

  return (
    <GlassCard>
      <h3 className="text-sm font-bold text-white mb-4 tracking-wide">{title}</h3>
      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
        {nodes.map(node => (
          <div
            key={node.id}
            className="group relative aspect-square rounded-md border border-white/5 transition-all hover:scale-110 hover:z-10 cursor-crosshair"
            style={{ backgroundColor: getStatusColor(node.status, node.value) }}
          >
            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max px-2 py-1 bg-slate-800 text-xs text-white rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              <span className="font-bold">{node.name}</span>
              <br />
              <span className="text-slate-300">Load: {Math.round(node.value * 100)}%</span>
            </div>
          </div>
        ))}
        {nodes.length === 0 && (
          <div className="col-span-full py-8 text-center text-xs text-slate-500">No nodes to display</div>
        )}
      </div>
    </GlassCard>
  );
});
LiveHeatmap.displayName = "LiveHeatmap";
