import axios from "axios";

export const apiClient = axios.create({
  baseURL: "",
  headers: { "Content-Type": "application/json" },
});

// ── Types ────────────────────────────────────────────────────────────────────

export interface ModelInfo {
  name: string;
  version: string;
  stage: string;
  registered_at: string | null;
  run_id: string | null;
  metrics: Record<string, number>;
}

export interface FeatureDrift {
  feature_name: string;
  psi: number;
  ks_statistic: number;
  ks_p_value: number;
  drifted: boolean;
}

export interface DriftReport {
  model_name: string;
  version: string;
  computed_at: string;
  total_predictions: number;
  drifted_features: number;
  features: FeatureDrift[];
}

export interface PredictResponse {
  model_name: string;
  model_version: string;   // actual version served ("1" or "2"), never "latest"
  ab_routed: boolean;
  predictions: (number | string)[];
  probabilities: number[][] | null;
  latency_ms: number;
}

export interface VersionStats {
  version: string;
  stage: string;
  count: number;
  traffic_pct: number;
  avg_latency_ms: number;
  labeled_count: number;
  accuracy: number | null;
}

export interface ABTestStats {
  model_name: string;
  split_percent: number;
  total_predictions: number;
  versions: VersionStats[];
}

// ── API calls ────────────────────────────────────────────────────────────────

export async function fetchModels(): Promise<ModelInfo[]> {
  const { data } = await apiClient.get<{ models: ModelInfo[] }>("/api/models/");
  return data.models;
}

export async function fetchDrift(
  modelName: string,
  version?: string,
  since?: string
): Promise<DriftReport> {
  const { data } = await apiClient.get<DriftReport>(`/api/drift/${modelName}`, {
    params: { ...(version ? { version } : {}), ...(since ? { since } : {}) },
  });
  return data;
}

export async function predict(
  modelName: string,
  features: number[],
  label?: number
): Promise<PredictResponse> {
  const { data } = await apiClient.post<PredictResponse>(
    `/api/predict/${modelName}`,
    { features, ...(label !== undefined ? { label } : {}) }
  );
  return data;
}

export async function fetchABStats(modelName: string): Promise<ABTestStats> {
  const { data } = await apiClient.get<ABTestStats>(`/api/ab-stats/${modelName}`);
  return data;
}
