import { useQuery } from "@tanstack/react-query";
import { fetchModels, fetchDrift, fetchABStats } from "../api/client";

export function useModels() {
  return useQuery({
    queryKey: ["models"],
    queryFn: fetchModels,
    refetchInterval: 30_000,
    retry: 2,
  });
}

export function useDrift(modelName: string | null, version?: string, since?: string) {
  return useQuery({
    queryKey: ["drift", modelName, version, since],
    queryFn: () => fetchDrift(modelName!, version, since),
    enabled: !!modelName,
    refetchInterval: 30_000,
  });
}

export function useABStats(modelName: string | null) {
  return useQuery({
    queryKey: ["ab-stats", modelName],
    queryFn: () => fetchABStats(modelName!),
    enabled: !!modelName,
    refetchInterval: 8_000,   // refresh quickly so live predictions show up
  });
}
