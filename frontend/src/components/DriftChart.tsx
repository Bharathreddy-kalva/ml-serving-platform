import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { FeatureDrift } from "../api/client";

interface Props {
  features: FeatureDrift[];
}

export function DriftChart({ features }: Props) {
  const driftedFeatures = features.filter((f) => f.drifted);
  const hasDrift = driftedFeatures.length > 0;

  return (
    <div>
      {/* ── Drift warning banner ── */}
      {hasDrift && (
        <div className="flex items-start gap-3 mb-5 p-4 bg-red-50 border border-red-300 rounded-xl">
          <span className="text-2xl leading-none mt-0.5">⚠</span>
          <div>
            <p className="font-semibold text-red-700 text-sm">Drift Detected</p>
            <p className="text-red-600 text-xs mt-0.5">
              {driftedFeatures.length} of {features.length} feature
              {driftedFeatures.length !== 1 ? "s have" : " has"} drifted beyond
              the PSI threshold (0.2):{" "}
              <span className="font-mono font-semibold">
                {driftedFeatures.map((f) => f.feature_name).join(", ")}
              </span>
            </p>
          </div>
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
        <BarChart
          data={features}
          margin={{ top: 4, right: 20, left: 0, bottom: 4 }}
        >
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
              <Cell
                key={i}
                fill={f.drifted ? "#ef4444" : "#3b82f6"}
                opacity={0.9}
              />
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
                  <span
                    className={`inline-flex items-center gap-1.5 font-mono ${
                      f.drifted ? "text-red-700" : "text-gray-700"
                    }`}
                  >
                    {f.drifted ? "🔴" : "🟢"}
                    {f.feature_name}
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
