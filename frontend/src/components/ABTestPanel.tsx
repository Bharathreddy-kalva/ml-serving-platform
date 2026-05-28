import React from "react";
import { useABStats } from "../hooks/useModels";
import type { VersionStats } from "../api/client";

const STAGE_COLOR: Record<string, string> = {
  Production: "text-emerald-700 bg-emerald-50 border-emerald-200",
  Staging: "text-amber-700 bg-amber-50 border-amber-200",
  None: "text-gray-500 bg-gray-100 border-gray-200",
};

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs py-1 border-b border-gray-50 last:border-0">
      <span className="text-gray-500">{label}</span>
      <span className="font-mono font-semibold text-gray-800">{value}</span>
    </div>
  );
}

function VersionBox({ stats, accent }: { stats: VersionStats; accent: "blue" | "emerald" }) {
  const accentRing = accent === "blue" ? "ring-blue-200 border-blue-300" : "ring-emerald-200 border-emerald-300";
  const accentBar  = accent === "blue" ? "bg-blue-500" : "bg-emerald-500";
  const stageStyle = STAGE_COLOR[stats.stage] ?? STAGE_COLOR.None;

  return (
    <div className={`rounded-xl border-2 p-4 ring-2 ${accentRing} bg-white`}>
      <div className="flex items-center justify-between mb-3">
        <span className="font-bold text-gray-900 text-sm">v{stats.version}</span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${stageStyle}`}>
          {stats.stage}
        </span>
      </div>

      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Traffic</span>
          <span className="font-semibold text-gray-700">{stats.traffic_pct.toFixed(1)}%</span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${accentBar}`}
            style={{ width: `${Math.min(stats.traffic_pct, 100)}%` }}
          />
        </div>
      </div>

      <div className="space-y-0">
        <StatRow label="Predictions" value={stats.count.toLocaleString()} />
        <StatRow label="Avg latency" value={stats.avg_latency_ms > 0 ? `${stats.avg_latency_ms.toFixed(1)} ms` : "–"} />
        <StatRow
          label="Accuracy"
          value={
            stats.accuracy != null
              ? `${(stats.accuracy * 100).toFixed(1)}%  (${stats.labeled_count} labeled)`
              : "–  no labels yet"
          }
        />
      </div>
    </div>
  );
}

interface Props {
  modelName: string;
}

export function ABTestPanel({ modelName }: Props) {
  const { data: stats, isLoading } = useABStats(modelName);

  if (isLoading) return null;
  if (!stats || stats.versions.length < 2) return null;

  const [v1, v2] = stats.versions;
  const totalCount = stats.total_predictions;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gray-900 text-white px-5 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold tracking-widest uppercase text-gray-400">A/B Test</span>
          <span className="text-sm font-semibold">{modelName}</span>
        </div>
        <div className="text-xs text-gray-400">
          Split:{" "}
          <span className="text-white font-mono">
            {stats.split_percent}% v{v1.version} / {100 - stats.split_percent}% v{v2.version}
          </span>
        </div>
      </div>

      <div className="p-5">
        {/* Version boxes */}
        <div className="grid grid-cols-2 gap-4 mb-5">
          <VersionBox stats={v1} accent="blue" />
          <VersionBox stats={v2} accent="emerald" />
        </div>

        {/* Combined traffic bar */}
        {totalCount > 0 && (
          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1.5">
              <span>v{v1.version} — {v1.count} requests</span>
              <span className="text-gray-400">{totalCount} total</span>
              <span>v{v2.version} — {v2.count} requests</span>
            </div>
            <div className="flex h-3 rounded-full overflow-hidden bg-gray-100">
              <div
                className="bg-blue-500 transition-all duration-700"
                style={{ width: `${(v1.count / Math.max(totalCount, 1)) * 100}%` }}
                title={`v${v1.version}: ${v1.count}`}
              />
              <div
                className="bg-emerald-500 transition-all duration-700"
                style={{ width: `${(v2.count / Math.max(totalCount, 1)) * 100}%` }}
                title={`v${v2.version}: ${v2.count}`}
              />
              {/* gap for un-logged traffic (should stay near 0) */}
            </div>
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-sm bg-blue-500 inline-block" />
                v{v1.version} Staging
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" />
                v{v2.version} Production
              </span>
            </div>
          </div>
        )}

        {totalCount === 0 && (
          <p className="text-center text-xs text-gray-400 py-2">
            No predictions yet — click "Predict Sample" on a model card above.
          </p>
        )}
      </div>
    </div>
  );
}
