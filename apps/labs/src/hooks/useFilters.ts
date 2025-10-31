'use client';

import { useCallback, useState } from "react";

export type ChamberFilter = "both" | "H" | "S";

export interface MetricToggles {
  totalRaised: boolean;
  totalDisbursed: boolean;
  cashOnHand: boolean;
}

export interface LeaderboardFilters {
  cycle: number;
  chamber: ChamberFilter;
  state: string;
  district: string;
  metrics: MetricToggles;
}

const DEFAULT_FILTERS: LeaderboardFilters = {
  cycle: 2026,
  chamber: "both",
  state: "all",
  district: "all",
  metrics: {
    totalRaised: true,
    totalDisbursed: true,
    cashOnHand: true,
  },
};

export function useFilters() {
  const [filters, setFilters] = useState<LeaderboardFilters>(DEFAULT_FILTERS);

  const updateFilter = useCallback(
    <K extends keyof LeaderboardFilters>(key: K, value: LeaderboardFilters[K]) => {
      setFilters((prev) => {
        const updated = { ...prev, [key]: value };

        if (key === "chamber" && value !== "H") {
          updated.district = "all";
        }

        if (key === "state") {
          updated.district = "all";
        }

        return updated;
      });
    },
    []
  );

  const updateMetric = useCallback((metric: keyof MetricToggles, value: boolean) => {
    setFilters((prev) => ({
      ...prev,
      metrics: {
        ...prev.metrics,
        [metric]: value,
      },
    }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  return {
    filters,
    updateFilter,
    updateMetric,
    resetFilters,
  };
}
