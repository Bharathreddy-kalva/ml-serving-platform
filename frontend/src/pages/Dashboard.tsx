import React, { useEffect, useRef, useState } from "react";
import { useModels, useDrift } from "../hooks/useModels";
import { ModelCard } from "../components/ModelCard";
import { DriftChart } from "../components/DriftChart";
import { ABTestPanel } from "../components/ABTestPanel";

function Spinner() {
  return (
    <div className="inline-block h-5 w-5 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
  );
}

interface SelectedCard { name: string; version: string }

export function Dashboard() {
  const { data: models, isLoading, error } = useModels();
  const [selected, setSelected] = useState<SelectedCard | null>(null);
  const hasAutoSelected = useRef(false);

  // Auto-open the drift section for the first model (v1 — where we send drift data)
  // Only fires once on initial load so user-driven changes aren't overridden.
  useEffect(() => {
    if (models && models.length > 0 && !hasAutoSelected.current) {
      const v1 = models.find((m) => m.version === "1") ?? models[0];
      setSelected({ name: v1.name, version: v1.version });
      hasAutoSelected.current = true;
    }
  }, [models]);

  const { data: drift, isLoading: driftLoading, dataUpdatedAt } = useDrift(
    selected?.name ?? null,
    selected?.version
  );

  const toggleCard = (name: string, version: string) =>
    setSelected((cur) =>
      cur?.name === name && cur?.version === version ? null : { name, version }
    );

  const modelNames = [...new Set(models?.map((m) => m.name) ?? [])];

  const lastRefreshed = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : null;

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Header */}
      <header className="bg-gray-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold tracking-tight">ML Serving Platform</h1>
            <p className="text-gray-400 text-xs mt-0.5">
              Model Monitoring · A/B Testing · Drift Detection
            </p>
          </div>
          <span className="text-xs text-gray-500 hidden sm:block font-mono bg-gray-800 px-2 py-1 rounded">
            :8000
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-10">

        {/* ── Model versions grid ── */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Model Versions
              {models && (
                <span className="ml-2 normal-case font-normal text-gray-400">
                  ({models.length})
                </span>
              )}
            </h2>
            {selected && (
              <button
                className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
                onClick={() => setSelected(null)}
              >
                Close drift ×
              </button>
            )}
          </div>

          {isLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {[1, 2].map((i) => (
                <div key={i} className="bg-white rounded-xl border-2 border-gray-200 h-52 animate-pulse" />
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
              <strong>Could not reach backend.</strong> Run{" "}
              <code className="font-mono text-xs bg-red-100 px-1 py-0.5 rounded">
                bash backend/run_dev.sh
              </code>
            </div>
          )}

          {models?.length === 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-10 text-center text-sm text-gray-500">
              No models found. Run{" "}
              <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">
                bash run_local.sh
              </code>
            </div>
          )}

          {models && models.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {models.map((m) => (
                <ModelCard
                  key={`${m.name}-${m.version}`}
                  model={m}
                  selected={selected?.name === m.name && selected?.version === m.version}
                  onClick={() => toggleCard(m.name, m.version)}
                />
              ))}
            </div>
          )}
        </section>

        {/* ── A/B Test panel ── */}
        {modelNames.map((name) => (
          <section key={name}>
            <ABTestPanel modelName={name} />
          </section>
        ))}

        {/* ── Drift section ── */}
        {selected && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
                Drift Report —{" "}
                <span className="text-blue-600 normal-case">
                  {selected.name} v{selected.version}
                </span>
              </h2>
              <div className="flex items-center gap-3 text-xs text-gray-400">
                {lastRefreshed && <span>Last updated: {lastRefreshed}</span>}
                <span className="text-gray-300">Auto-refreshes every 30 s</span>
              </div>
            </div>

            {driftLoading && !drift && (
              <div className="bg-white rounded-xl border border-gray-200 p-10 flex flex-col items-center gap-3 text-sm text-gray-500">
                <Spinner />
                Computing drift…
              </div>
            )}

            {drift && drift.features.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                {/* Summary bar */}
                <div className="flex flex-wrap items-center gap-3 mb-6">
                  <span className="text-sm text-gray-600">
                    <span className="font-semibold text-gray-900">
                      {drift.total_predictions}
                    </span>{" "}
                    predictions analysed
                  </span>
                  <span
                    className={`text-xs font-medium px-3 py-1 rounded-full ${
                      drift.drifted_features > 0
                        ? "bg-red-100 text-red-700"
                        : "bg-emerald-100 text-emerald-700"
                    }`}
                  >
                    {drift.drifted_features === 0
                      ? "✓ No drift detected"
                      : `⚠ ${drift.drifted_features} feature(s) drifted`}
                  </span>
                  {driftLoading && (
                    <span className="text-gray-400 text-xs flex items-center gap-1">
                      <span className="inline-block h-3 w-3 rounded-full border border-blue-400 border-t-transparent animate-spin" />
                      refreshing…
                    </span>
                  )}
                </div>

                <DriftChart features={drift.features} />
              </div>
            )}

            {drift && drift.features.length === 0 && !driftLoading && (
              <div className="bg-white rounded-xl border border-gray-200 p-10 text-center">
                <p className="text-sm text-gray-500">
                  Not enough predictions to compute drift yet.
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {drift.total_predictions === 0
                    ? "Run: .venv/bin/python ml/scripts/simulate_drift.py"
                    : `${drift.total_predictions} prediction(s) logged — need at least 4.`}
                </p>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
