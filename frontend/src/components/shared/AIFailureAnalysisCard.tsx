
import { motion } from "framer-motion";
import { BrainCircuit, AlertTriangle, CheckCircle2, RotateCcw, XCircle, Info, Database, ShieldAlert, Network, Cog } from "lucide-react";
import { AIFailureAnalysis } from "../../services/jobs.service";
import { cn } from "../../utils/cn";

interface AIFailureAnalysisCardProps {
  analysis: AIFailureAnalysis;
  className?: string;
}

export function AIFailureAnalysisCard({ analysis, className }: AIFailureAnalysisCardProps) {
  // Map category to color and icon
  const getCategoryTheme = (category: string) => {
    switch (category.toLowerCase()) {
      case "authentication":
        return { color: "text-red-400", border: "border-red-500/20", bg: "bg-red-500/10", icon: ShieldAlert, glow: "shadow-[0_0_15px_rgba(239,68,68,0.1)]" };
      case "database":
        return { color: "text-orange-400", border: "border-orange-500/20", bg: "bg-orange-500/10", icon: Database, glow: "shadow-[0_0_15px_rgba(249,115,22,0.1)]" };
      case "network":
        return { color: "text-yellow-400", border: "border-yellow-500/20", bg: "bg-yellow-500/10", icon: Network, glow: "shadow-[0_0_15px_rgba(234,179,8,0.1)]" };
      case "validation":
        return { color: "text-blue-400", border: "border-blue-500/20", bg: "bg-blue-500/10", icon: AlertTriangle, glow: "shadow-[0_0_15px_rgba(59,130,246,0.1)]" };
      case "internal":
      default:
        return { color: "text-purple-400", border: "border-purple-500/20", bg: "bg-purple-500/10", icon: Cog, glow: "shadow-[0_0_15px_rgba(168,85,247,0.1)]" };
    }
  };

  const theme = getCategoryTheme(analysis.error_category);
  const Icon = theme.icon;

  const confidencePct = Math.round(analysis.confidence_score * 100);
  const confidenceColor = confidencePct > 90 ? "bg-green-500" : confidencePct > 70 ? "bg-yellow-500" : "bg-orange-500";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "glass-card border rounded-2xl p-5 md:p-6 overflow-hidden relative",
        theme.border,
        theme.glow,
        className
      )}
    >
      {/* Background decoration */}
      <div className={cn("absolute -top-10 -right-10 w-40 h-40 rounded-full blur-3xl opacity-20", theme.bg)} />

      <div className="flex items-start gap-4 mb-6 relative">
        <div className={cn("h-12 w-12 rounded-xl flex items-center justify-center shrink-0 border backdrop-blur-sm", theme.bg, theme.border)}>
          <Icon className={cn("h-6 w-6", theme.color)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              AI Failure Analysis
            </h3>
            <span className={cn("text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full border", theme.bg, theme.color, theme.border)}>
              {analysis.error_category}
            </span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed font-medium">
            {analysis.failure_summary}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative">
        {/* Left Column */}
        <div className="space-y-6">
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <AlertTriangle className="h-4 w-4 text-slate-400" />
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Root Cause</h4>
            </div>
            <p className="text-sm text-slate-200 bg-white/5 border border-white/5 rounded-xl p-3 leading-relaxed">
              {analysis.root_cause}
            </p>
          </div>

          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <CheckCircle2 className="h-4 w-4 text-slate-400" />
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Suggested Fixes</h4>
            </div>
            <ul className="space-y-2">
              {analysis.suggested_fixes.map((fix, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="text-blue-400 mt-0.5 font-bold">•</span>
                  <span className="leading-relaxed">{fix}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <BrainCircuit className="h-4 w-4 text-slate-400" />
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Confidence Score</h4>
              </div>
              <span className="text-xs font-bold text-white">{confidencePct}%</span>
            </div>
            <div className="h-2 w-full bg-[#0a1020] rounded-full overflow-hidden border border-white/5 relative">
              <motion.div 
                initial={{ width: 0 }} 
                animate={{ width: `${confidencePct}%` }} 
                transition={{ duration: 1, ease: "easeOut" }}
                className={cn("absolute inset-y-0 left-0 rounded-full", confidenceColor)} 
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/5 border border-white/5 rounded-xl p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <RotateCcw className="h-4 w-4 text-slate-400" />
                <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Retry Action</h4>
              </div>
              <div className="flex items-center gap-2">
                {analysis.retry_recommendation ? (
                  <><CheckCircle2 className="h-4 w-4 text-green-400" /> <span className="text-sm font-semibold text-green-400">Recommended</span></>
                ) : (
                  <><XCircle className="h-4 w-4 text-red-400" /> <span className="text-sm font-semibold text-red-400">Avoid</span></>
                )}
              </div>
            </div>

            <div className="bg-white/5 border border-white/5 rounded-xl p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Info className="h-4 w-4 text-slate-400" />
                <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Est. Recovery</h4>
              </div>
              <span className="text-sm font-semibold text-white">{analysis.estimated_recovery}</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
