import React, { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Cell,
} from "recharts";
import { triggerRetrain, type FeatureDrift } from "../api/client";

interface Toast { msg: string; kind: "success" | "error" }

interface Props {
  features: FeatureDrift[];
  modelName: string;
  modelVersion: string;
}

export function DriftChart({ features, modelName, modelVersion }: Props) {
  const queryClient = useQueryClient();
  const [toast, setToast] = useState<Toast | null>(null);

  const retrain = useMutation({
    mutationFn: () => triggerRetrain(modelName, modelVersion),
    onSuccess: (event) => {
      const label = event.new_version
        ? `v${event.new_version} trained in ${event.duration_seconds?.toFixed(1)}s`
        : "Retraining completed";
      setToast({ msg: `✓ ${label}`, kind: "success" });
      queryClient.invalidateQueries({ queryKey: ["retrain-log"] });
      queryClient.invalidateQueries({ queryKey: ["models"] });
    },
    onError: (err: Error) => {
      setToast({ msg: `✗ Retraining failed: ${err.message}`, kind: "error" });
    },
  });

  // Auto-dismiss toast after 5 s
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 5_000);
    return () => clearTimeout(t);
  }, [toast]);

  const driftedFeatures = features.filter((f) => f.drifted);
  const hasDrift = driftedFeatures.length > 0;

  return (
    <div>
      {/* ── Toast (viewport-fixed) ── */}
      {toast && (
        <div
          className={`fixed bottom-5 right-5 z-50 max-w-sm px-4 py-3 rounded-xl shadow-xl
            text-sm font-medium transition-all ${
              toast.kind === "success"
                ? "bg-emerald-600 text-white"
                : "bg-red-600 text-white"
            }`}
        >
          {toast.msg}
        </div>
      )}

      {/* ── Drift warning banner ── */}
      {hasDrift && (
        <div className="flex items-start justify-between gap-4 mb-5 p-4 bg-red-50 border border-red-300 rounded-xl">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <span className="text-2xl leading-none mt-0.5 shrink-0">⚠</span>
            <div className="min-w-0">
              <p className="font-semibold text-red-700 text-sm">
                Drift Detected —{" "}
                <span className="font-normal text-red-500">
                  Auto-retrain scheduled
                </span>
              </p>
              <p className="text-red-600 text-xs mt-0.5 leading-relaxed">
                {driftedFeatures.length} of {features.length} feature
                {driftedFeatures.length !== 1 ? "s have" : " has"} drifted
                beyond the PSI threshold (0.2):{" "}
                <span className="font-mono font-semibold">
                  {driftedFeatures.map((f) => f.feature_name).join(", ")}
                </span>
              </p>
            </div>
          </div>

          {/* Retrain button */}
          <button
            className="shrink-0 flex items-center gap-1.5 text-xs font-semibold
              px-3 py-1.5 rounded-lg border transition-all
              bg-red-600 text-white border-red-700
              hover:bg-red-700 active:scale-95
              disabled:opacity-60 disabled:cursor-not-allowed"
            onClick={() => retrain.mutate()}
            disabled={retrain.isPending}
            title="Manually trigger retraining now"
          >
            {retrain.isPending ? (
              <>
                <span className="inline-block h-3.5 w-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                Retraining…
              </>
            ) : (
              <>↻ Trigger Retrain</>
            )}
          </button>
        </div>
      )}

      {/* ── Legend ── */}
      <div className="flex items-center gap-4 mb-3 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-blue-500" />
          Stable (PSI ≤ 0.2)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-red-500" />
          Drifted (PSI &gt; 0.2)
        </span>
      </div>

      {/* ── Bar chart ── */}
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={features} margin={{ top: 4, right: 20, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis
            dataKey="feature_name"
            tick={{ fontSize: 11, fill: "#6b7280" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#6b7280" }}
            axisLine={false}
            tickLine={false}
            width={44}
            tickFormatter={(v: number) => v.toFixed(1)}
          />
          <Tooltip
            formatter={(value: unknown) => [
              typeof value === "number" ? value.toFixed(4) : String(value),
              "PSI",
            ]}
            labelFormatter={(label) => `Feature: ${label}`}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e5e7eb",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            }}
          />
          <ReferenceLine
            y={0.2}
            stroke="#ef4444"
            strokeDasharray="5 3"
            strokeWidth={1.5}
            label={{
              value: "threshold 0.2",
              position: "insideTopRight",
              fontSize: 10,
              fill: "#ef4444",
              dx: -4,
            }}
          />
          <Bar dataKey="psi" name="PSI" radius={[4, 4, 0, 0]} maxBarSize={72}>
            {features.map((f, i) => (
              <Cell key={i} fill={f.drifted ? "#ef4444" : "#3b82f6"} opacity={0.9} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* ── Per-feature table ── */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-xs text-left border-collapse">
          <thead>
            <tr className="text-gray-400 uppercase tracking-wide">
              <th className="pb-2 pr-4 font-medium">Feature</th>
              <th className="pb-2 pr-4 font-medium text-right">PSI</th>
              <th className="pb-2 pr-4 font-medium text-right">KS stat</th>
              <th className="pb-2 font-medium text-right">KS p-value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {features.map((f) => (
              <tr key={f.feature_name} className={f.drifted ? "bg-red-50/50" : ""}>
                <td className="py-1.5 pr-4">
                  <span className={`inline-flex items-center gap-1.5 font-mono ${f.drifted ? "text-red-700" : "text-gray-700"}`}>
                    {f.drifted ? "🔴" : "🟢"} {f.feature_name}
                  </span>
                </td>
                <td className={`py-1.5 pr-4 text-right font-semibold font-mono ${f.drifted ? "text-red-600" : "text-gray-700"}`}>
                  {f.psi.toFixed(4)}
                </td>
                <td className="py-1.5 pr-4 text-right font-mono text-gray-500">
                  {f.ks_statistic.toFixed(4)}
                </td>
                <td className="py-1.5 text-right font-mono text-gray-500">
                  {f.ks_p_value.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
