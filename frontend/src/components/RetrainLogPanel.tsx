import React from "react";
import { useRetrainLog } from "../hooks/useModels";
import type { RetrainEvent } from "../api/client";

function StatusPill({ status }: { status: RetrainEvent["status"] }) {
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
        status === "success"
          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
          : "bg-red-50 text-red-600 border border-red-200"
      }`}
    >
      {status === "success" ? "✓ success" : "✗ failed"}
    </span>
  );
}

function TriggerPill({ trigger }: { trigger: RetrainEvent["trigger"] }) {
  return (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
        trigger === "auto"
          ? "bg-purple-50 text-purple-700 border-purple-200"
          : "bg-blue-50 text-blue-600 border-blue-200"
      }`}
    >
      {trigger}
    </span>
  );
}

export function RetrainLogPanel() {
  const { data, isLoading } = useRetrainLog();

  if (isLoading) return null;
  if (!data || data.events.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
          Retraining Log
        </h2>
        <p className="text-sm text-gray-400">
          No retraining events yet. Drift detection runs every 60 s, or use the
          "Trigger Retrain" button on the drift banner.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Retraining Log
        </h2>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          {data.retrain_in_progress && (
            <span className="flex items-center gap-1.5 text-amber-600 font-medium">
              <span className="inline-block h-3 w-3 rounded-full border-2 border-amber-500 border-t-transparent animate-spin" />
              Retraining in progress…
            </span>
          )}
          <span>{data.events.length} event{data.events.length !== 1 ? "s" : ""}</span>
        </div>
      </div>

      {/* Events */}
      <div className="divide-y divide-gray-50">
        {data.events.map((ev) => (
          <div key={ev.id} className="px-5 py-3.5 flex flex-wrap items-start gap-x-4 gap-y-1">
            {/* Left: timestamp + trigger */}
            <div className="w-36 shrink-0">
              <p className="text-xs font-mono text-gray-500">
                {new Date(ev.timestamp).toLocaleTimeString()}
              </p>
              <p className="text-xs text-gray-400">
                {new Date(ev.timestamp).toLocaleDateString()}
              </p>
            </div>

            {/* Middle: model + reason */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-xs font-semibold text-gray-800">
                  {ev.model_name}
                </span>
                <span className="text-gray-300 text-xs">v{ev.triggered_by_version}</span>
                <TriggerPill trigger={ev.trigger} />
                <StatusPill status={ev.status} />
              </div>
              <p className="text-xs text-gray-500 truncate">{ev.reason}</p>
              {ev.error && (
                <p className="text-xs text-red-500 mt-0.5 font-mono">{ev.error}</p>
              )}
            </div>

            {/* Right: new version + duration */}
            <div className="text-right shrink-0">
              {ev.new_version && (
                <p className="text-xs font-semibold text-emerald-600">
                  → v{ev.new_version}
                </p>
              )}
              {ev.duration_seconds != null && (
                <p className="text-xs text-gray-400 font-mono">
                  {ev.duration_seconds.toFixed(1)}s
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
