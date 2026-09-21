import React from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend
} from "recharts";
import { GlassCard } from "../shared/GlassCard";

interface ChartDataPoint {
  time: string;
  [key: string]: any;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card px-3 py-2.5 rounded-xl text-xs shadow-2xl backdrop-blur-xl border border-white/10 bg-[#030712]/90">
      <p className="text-slate-400 mb-1">{label}</p>
      {payload.map((e: any, i: number) => (
        <p key={i} className="font-semibold font-mono" style={{ color: e.color }}>
          {e.name}: {e.value}
        </p>
      ))}
    </div>
  );
}

export const MemoizedAreaChart = React.memo(({ data, title, dataKeys, colors }: { 
  data: ChartDataPoint[], 
  title: string,
  dataKeys: string[],
  colors: string[]
}) => {
  return (
    <GlassCard>
      <h3 className="text-sm font-bold text-white mb-4 tracking-wide">{title}</h3>
      <div className="h-52">
        <ResponsiveContainer>
          <AreaChart data={data}>
            <defs>
              {dataKeys.map((key, i) => (
                <linearGradient key={key} id={`color${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={colors[i]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={colors[i]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
            <XAxis dataKey="time" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} minTickGap={20} />
            <YAxis stroke="#475569" fontSize={10} tickLine={false} axisLine={false} width={30} />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(255,255,255,0.1)", strokeWidth: 2 }} />
            <Legend wrapperStyle={{ fontSize: "10px", color: "#94a3b8" }} />
            {dataKeys.map((key, i) => (
              <Area 
                key={key} type="monotone" dataKey={key} stroke={colors[i]} strokeWidth={2}
                fillOpacity={1} fill={`url(#color${key})`} isAnimationActive={false}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </GlassCard>
  );
});
MemoizedAreaChart.displayName = "MemoizedAreaChart";

export const MemoizedBarChart = React.memo(({ data, title, dataKeys, colors, unit = "" }: {
  data: any[], title: string, dataKeys: string[], colors: string[], unit?: string
}) => {
  return (
    <GlassCard>
      <h3 className="text-sm font-bold text-white mb-4 tracking-wide">{title}</h3>
      <div className="h-52">
        {data.length > 0 ? (
          <ResponsiveContainer>
            <BarChart data={data} barSize={12} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="name" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="#475569" fontSize={10} tickLine={false} axisLine={false} width={30} unit={unit} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
              <Legend wrapperStyle={{ fontSize: "10px", color: "#64748b" }} />
              {dataKeys.map((key, i) => (
                <Bar key={key} dataKey={key} fill={colors[i]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm">No data available</div>
        )}
      </div>
    </GlassCard>
  );
});
MemoizedBarChart.displayName = "MemoizedBarChart";
