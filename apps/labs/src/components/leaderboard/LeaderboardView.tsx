'use client';

import { useMemo, useState } from "react";
import { useFilters, type ChamberFilter } from "@/hooks/useFilters";
import { useCandidateData } from "@/hooks/useCandidateData";
import { RaceTable } from "@/components/leaderboard/RaceTable";
import { RaceChart } from "@/components/leaderboard/RaceChart";
import { RaceTreemap } from "@/components/leaderboard/RaceTreemap";
import { ExportButton } from "@/components/leaderboard/ExportButton";
import { formatRelativeTime } from "@/utils/formatters";
import { MultiSelect, type MultiSelectOption } from "@/components/shared/MultiSelect";

const US_STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
];

const CYCLES = [2026, 2024];

const PARTY_OPTIONS: MultiSelectOption[] = [
  { value: "democrat", label: "Democratic" },
  { value: "republican", label: "Republican" },
  { value: "other", label: "Other" },
];

const METRIC_OPTIONS: MultiSelectOption[] = [
  { value: "totalRaised", label: "Total Raised" },
  { value: "totalDisbursed", label: "Total Spent" },
  { value: "cashOnHand", label: "Cash on Hand" },
];

type ViewMode = "table" | "chart" | "treemap";

export function LeaderboardView() {
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [selectedParties, setSelectedParties] = useState<string[]>([
    "democrat",
    "republican",
    "other",
  ]);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([
    "totalRaised",
  ]);

  const { filters, updateFilter, resetFilters } = useFilters();
  const { data, loading, error, lastUpdated } = useCandidateData(filters);

  const filteredData = useMemo(() => {
    return data.filter((candidate) => {
      const normalized = (candidate.party ?? "").toLowerCase();
      const isDem = normalized.includes("dem");
      const isGop = normalized.includes("rep") || normalized.includes("gop");
      if (isDem) return selectedParties.includes("democrat");
      if (isGop) return selectedParties.includes("republican");
      return selectedParties.includes("other");
    });
  }, [data, selectedParties]);

  // Convert selected metrics to filter format
  const metricsFilter = useMemo(() => ({
    totalRaised: selectedMetrics.includes("totalRaised"),
    totalDisbursed: selectedMetrics.includes("totalDisbursed"),
    cashOnHand: selectedMetrics.includes("cashOnHand"),
  }), [selectedMetrics]);

  const handleResetAll = () => {
    resetFilters();
    setSelectedParties(["democrat", "republican", "other"]);
    setSelectedMetrics(["totalRaised"]);
  };

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <h1 className="font-display text-3xl font-semibold text-gray-900">
              Campaign Finance Leaderboard
            </h1>
            <p className="text-sm text-gray-600">
              View the top raisers, spenders, and hoarders.
            </p>
          </div>
          <div className="flex w-full justify-end lg:w-auto">
            <div className="inline-flex items-center gap-2 border border-green-600 bg-green-50 px-3 py-1.5 text-xs text-green-700">
              <span className="h-1.5 w-1.5 bg-green-600"></span>
              {loading
                ? "Loading data..."
                : lastUpdated
                ? `Data updated: ${formatRelativeTime(lastUpdated)}`
                : "Awaiting update"}
            </div>
          </div>
        </div>
      </header>

      <section className="border-2 border-rb-brand-navy bg-white p-6 text-gray-900">
        <div className="flex justify-end">
          <button
            onClick={handleResetAll}
            className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.25rem] text-gray-600 transition hover:text-rb-brand-navy"
          >
            Reset All
          </button>
        </div>

        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-start">
          <div className="flex flex-col gap-2 w-full sm:w-[140px]">
            <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
              Cycle
            </label>
            <div className="relative">
              <select
                value={filters.cycle}
                onChange={(event) => updateFilter("cycle", Number(event.target.value))}
                className="h-[42px] w-full appearance-none border border-gray-300 bg-white px-4 pr-10 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none"
              >
                {CYCLES.map((cycle) => (
                  <option key={cycle} value={cycle}>
                    {cycle}
                  </option>
                ))}
              </select>
              <svg
                className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div className="flex flex-col gap-2 w-full sm:w-[140px]">
            <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
              Chamber
            </label>
            <div className="relative">
              <select
                value={filters.chamber}
                onChange={(event) => updateFilter("chamber", event.target.value as ChamberFilter)}
                className="h-[42px] w-full appearance-none border border-gray-300 bg-white px-4 pr-10 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none"
              >
                <option value="both">Both</option>
                <option value="H">House</option>
                <option value="S">Senate</option>
              </select>
              <svg
                className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div className="flex flex-col gap-2 w-full sm:w-[140px]">
            <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
              State
            </label>
            <div className="relative">
              <select
                value={filters.state}
                onChange={(event) => updateFilter("state", event.target.value)}
                className="h-[42px] w-full appearance-none border border-gray-300 bg-white px-4 pr-10 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none"
              >
                <option value="all">All States</option>
                {US_STATES.map((state) => (
                  <option key={state} value={state}>
                    {state}
                  </option>
                ))}
              </select>
              <svg
                className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          <div className="w-full sm:max-w-[200px]">
            <MultiSelect
              label="Party"
              options={PARTY_OPTIONS}
              selected={selectedParties}
              onChange={setSelectedParties}
              placeholder="Select parties"
            />
          </div>

          <div className="w-full sm:max-w-[200px]">
            <MultiSelect
              label="Metrics"
              options={METRIC_OPTIONS}
              selected={selectedMetrics}
              onChange={setSelectedMetrics}
              placeholder="Select metrics"
            />
          </div>
        </div>
      </section>

      <section className="border-2 border-rb-brand-navy bg-white">
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 sm:p-6">
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={() => setViewMode("table")}
              className={`rounded-lg px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold uppercase tracking-[0.1rem] sm:tracking-[0.2rem] transition ${
                viewMode === "table"
                  ? "bg-rb-gold text-rb-brand-navy"
                  : "bg-white text-gray-600 hover:text-rb-brand-navy"
              }`}
            >
              <span className="inline-flex items-center gap-1.5 sm:gap-2">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span className="hidden sm:inline">Table</span>
              </span>
            </button>
            <button
              onClick={() => setViewMode("chart")}
              className={`rounded-lg px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold uppercase tracking-[0.1rem] sm:tracking-[0.2rem] transition ${
                viewMode === "chart"
                  ? "bg-rb-gold text-rb-brand-navy"
                  : "bg-white text-gray-600 hover:text-rb-brand-navy"
              }`}
            >
              <span className="inline-flex items-center gap-1.5 sm:gap-2">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span className="hidden sm:inline">Chart</span>
              </span>
            </button>
            <button
              onClick={() => setViewMode("treemap")}
              className={`rounded-lg px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold uppercase tracking-[0.1rem] sm:tracking-[0.2rem] transition ${
                viewMode === "treemap"
                  ? "bg-rb-gold text-rb-brand-navy"
                  : "bg-white text-gray-600 hover:text-rb-brand-navy"
              }`}
            >
              <span className="inline-flex items-center gap-1.5 sm:gap-2">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 12a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1v-7z" />
                </svg>
                <span className="hidden sm:inline">Treemap</span>
              </span>
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3 sm:gap-4">
            <span className="text-xs uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-rb-grey">
              {loading
                ? "Loading..."
                : `Showing ${filteredData.length.toLocaleString()} candidates`}
            </span>
            <ExportButton
              data={filteredData}
              metrics={metricsFilter}
              disabled={loading || filteredData.length === 0}
            />
          </div>
        </div>

        <div className="border-t border-rb-border">
          {error ? (
            <div className="p-12 text-center text-sm text-rb-red">
              Error loading data: {error}
            </div>
          ) : loading ? (
            <div className="p-12 text-center text-sm text-rb-grey">
              Loading campaign finance data…
            </div>
          ) : viewMode === "table" ? (
            <div className="w-full overflow-x-auto">
              <div className="min-w-[800px]">
                <RaceTable data={filteredData} metrics={metricsFilter} />
              </div>
            </div>
          ) : viewMode === "chart" ? (
            <div className="p-6">
              <RaceChart data={filteredData} metrics={metricsFilter} />
            </div>
          ) : (
            <div className="p-6">
              <RaceTreemap data={filteredData} metrics={metricsFilter} />
            </div>
          )}
        </div>
      </section>
    </section>
  );
}
