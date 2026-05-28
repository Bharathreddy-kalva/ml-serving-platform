import React from "react";
import { useMutation } from "@tanstack/react-query";
import { predict, type ModelInfo } from "../api/client";

const SAMPLE_FEATURES = [5.1, 3.5, 1.4, 0.2];   // Iris setosa — label 0
const SAMPLE_LABEL = 0;
const IRIS_CLASS_NAMES = ["Setosa", "Versicolor", "Virginica"] as const;

const STAGE_PILL: Record<string, string> = {
  Production: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Staging:    "bg-amber-50  text-amber-700  border-amber-200",
  None:       "bg-gray-100  text-gray-500   border-gray-200",
  Archived:   "bg-red-50    text-red-600    border-red-200",
};

const METRIC_LABELS: Record<string, string> = {
  test_accuracy:    "Test accuracy",
  cv_accuracy_mean: "CV accuracy",
};

interface Props {
  model: ModelInfo;
  selected: boolean;
  onClick: () => void;
}

export function ModelCard({ model, selected, onClick }: Props) {
  const { mutate, isPending, data: result, error, reset } = useMutation({
    mutationFn: () => predict(model.name, SAMPLE_FEATURES, SAMPLE_LABEL),
  });

  const pillStyle   = STAGE_PILL[model.stage] ?? STAGE_PILL.None;
  const borderStyle = selected
    ? "border-blue-500 ring-2 ring-blue-100 shadow-md"
    : "border-gray-200 hover:border-gray-300 hover:shadow-sm";

  const displayMetrics = Object.entries(model.metrics).filter(([k]) =>
    Object.keys(METRIC_LABELS).includes(k)
  );

  const predIdx   = result ? (result.predictions[0] as number) : null;
  const predClass = predIdx != null ? (IRIS_CLASS_NAMES[predIdx] ?? `Class ${predIdx}`) : null;
  const predConf  = result?.probabilities != null && predIdx != null
    ? result.probabilities[0][predIdx]
    : null;

  return (
    <div
      className={`bg-white rounded-xl border-2 p-5 cursor-pointer transition-all ${borderStyle}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
    >
      {/* Name + stage */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <h3 className="font-semibold text-gray-900 text-sm leading-snug truncate">
          {model.name}
        </h3>
        <span className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border ${pillStyle}`}>
          {model.stage}
        </span>
      </div>

      <p className="text-xs text-gray-400 mb-3">v{model.version}</p>

      {/* Metrics */}
      {displayMetrics.length > 0 && (
        <div className="space-y-1 mb-4">
          {displayMetrics.map(([k, v]) => (
            <div key={k} className="flex justify-between text-xs text-gray-600">
              <span>{METRIC_LABELS[k]}</span>
              <span className="font-mono font-semibold text-gray-800">
                {(v * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Predict area — clicks don't propagate to the card toggle */}
      <div className="border-t border-gray-100 pt-3" onClick={(e) => e.stopPropagation()}>
        <div className="flex gap-2">
          <button
            className="flex-1 text-xs font-medium bg-blue-600 text-white py-1.5 px-3 rounded-lg
                       hover:bg-blue-700 active:scale-95 transition-all
                       disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={() => { reset(); mutate(); }}
            disabled={isPending}
          >
            {isPending ? "Predicting…" : "Predict Sample"}
          </button>
          {result && (
            <button
              className="text-xs text-gray-400 hover:text-gray-600 px-1"
              onClick={reset}
              title="Clear"
            >
              ×
            </button>
          )}
        </div>

        {/* Result */}
        {result && (
          <div className="mt-2 p-2.5 bg-blue-50 rounded-lg text-xs space-y-0.5">
            <div className="font-semibold text-blue-800">{predClass}</div>
            {predConf != null && (
              <div className="text-blue-600">
                Confidence:{" "}
                <span className="font-mono">{(predConf * 100).toFixed(1)}%</span>
              </div>
            )}
            <div className="text-gray-400 font-mono">{result.latency_ms.toFixed(1)} ms</div>
            {/* Show which version the A/B router actually picked */}
            {result.ab_routed && (
              <div className="mt-1 pt-1 border-t border-blue-100 text-blue-500 font-mono">
                ↳ served by v{result.model_version}
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-2 p-2 bg-red-50 rounded-lg text-xs text-red-600 border border-red-100">
            Predict failed — is the backend running?
          </div>
        )}

        <p className="mt-1.5 text-gray-300 text-xs">
          Sample: {SAMPLE_FEATURES.join(", ")}
        </p>
      </div>
    </div>
  );
}
