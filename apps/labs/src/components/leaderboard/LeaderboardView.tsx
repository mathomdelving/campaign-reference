'use client';

import { useMemo, useState } from "react";
import { useFilters, type ChamberFilter } from "@/hooks/useFilters";
import { useCandidateData } from "@/hooks/useCandidateData";
import { RaceTable } from "@/components/leaderboard/RaceTable";
import { RaceChart } from "@/components/leaderboard/RaceChart";
import { ExportButton } from "@/components/leaderboard/ExportButton";
import { formatRelativeTime } from "@/utils/formatters";

const US_STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
];

const CYCLES = [2026, 2024, 2022];

type ViewMode = "table" | "chart";

export function LeaderboardView() {
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [partySelection, setPartySelection] = useState({
    democrat: true,
    republican: true,
    other: true,
  });
  const partyOptions: Array<{ key: keyof typeof partySelection; label: string }> = [
    { key: "democrat", label: "Dem" },
    { key: "republican", label: "GOP" },
    { key: "other", label: "Other" },
  ];
  const { filters, updateFilter, updateMetric, resetFilters } = useFilters();
  const { data, loading, error, lastUpdated } = useCandidateData(filters);

  const filteredData = useMemo(() => {
    return data.filter((candidate) => {
      const normalized = (candidate.party ?? "").toLowerCase();
      const isDem = normalized.includes("democrat");
      const isGop = normalized.includes("republican");
      if (isDem) return partySelection.democrat;
      if (isGop) return partySelection.republican;
      return partySelection.other;
    });
  }, [data, partySelection]);

  const handlePartyToggle = (key: keyof typeof partySelection) => {
    setPartySelection((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
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
            onClick={resetFilters}
            className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.25rem] text-gray-600 transition hover:text-rb-brand-navy"
          >
            Reset All
          </button>
        </div>

        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
              Cycle
            </label>
            <select
              value={filters.cycle}
              onChange={(event) => updateFilter("cycle", Number(event.target.value))}
              className="h-[42px] w-full border border-gray-300 bg-white px-4 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none"
            >
              {CYCLES.map((cycle) => (
                <option key={cycle} value={cycle}>
                  {cycle}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-2 sm:col-span-2 lg:col-span-1">
            <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
              Chamber
            </label>
            <div className="flex h-[42px] gap-2">
              {(
                [
                  { value: "both" as ChamberFilter, label: "Both" },
                  { value: "H" as ChamberFilter, label: "House" },
                  { value: "S" as ChamberFilter, label: "Senate" },
                ] satisfies Array<{ value: ChamberFilter; label: string }>
              ).map((option) => {
                const active = filters.chamber === option.value;
                return (
                  <button
                    key={option.value}
                    onClick={() => updateFilter("chamber", option.value)}
                    className={[
                      "flex-1 px-3 text-sm font-medium transition",
                      active
                        ? "bg-rb-gold text-rb-brand-navy"
                        : "border border-gray-300 bg-white text-gray-600 hover:border-rb-brand-navy hover:text-rb-brand-navy",
                    ].join(" ")}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
              State
            </label>
            <select
              value={filters.state}
              onChange={(event) => updateFilter("state", event.target.value)}
              className="h-[42px] w-full border border-gray-300 bg-white px-4 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none"
            >
              <option value="all">All States</option>
              {US_STATES.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-2 sm:col-span-2 lg:col-span-1">
            <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
              Party Filter
            </label>
            <div className="flex h-[42px] gap-2">
              {partyOptions.map(({ key, label }) => {
                const active = partySelection[key];
                return (
                  <button
                    key={key}
                    onClick={() => handlePartyToggle(key)}
                    className={[
                      "flex-1 border border-gray-300 px-3 text-sm font-medium transition",
                      active
                        ? "bg-rb-gold text-rb-brand-navy border-rb-gold"
                        : "bg-white text-gray-600 hover:border-rb-brand-navy hover:text-rb-brand-navy",
                    ].join(" ")}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {[
            { key: "totalRaised", label: "Total Raised" },
            { key: "totalDisbursed", label: "Total Spent" },
            { key: "cashOnHand", label: "Cash on Hand" },
          ].map(({ key, label }) => {
            const active = filters.metrics[key as keyof typeof filters.metrics];
            return (
              <button
                key={key}
                onClick={() =>
                  updateMetric(key as keyof typeof filters.metrics, !active)
                }
                className={[
                  "h-[42px] px-4 text-sm font-medium transition-colors duration-150",
                  active
                    ? "bg-rb-gold text-rb-brand-navy"
                    : "bg-rb-brand-navy text-white hover:bg-rb-blue",
                ].join(" ")}
              >
                {label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="border-2 border-rb-brand-navy bg-white">
        <div className="flex flex-wrap items-center justify-between gap-4 p-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setViewMode("table")}
              className={`px-4 py-2 text-sm font-semibold uppercase tracking-[0.2rem] transition ${
                viewMode === "table"
                  ? "bg-rb-gold text-rb-brand-navy"
                  : "text-gray-600 hover:text-rb-brand-navy"
              }`}
            >
              <span className="inline-flex items-center gap-2">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Table
              </span>
            </button>
            <button
              onClick={() => setViewMode("chart")}
              className={`rounded-lg px-4 py-2 text-sm font-semibold uppercase tracking-[0.2rem] transition ${
                viewMode === "chart"
                  ? "bg-rb-red text-white"
                  : "text-rb-grey hover:text-rb-brand-navy"
              }`}
            >
              <span className="inline-flex items-center gap-2">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Chart
              </span>
            </button>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-xs uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-rb-grey">
              {loading
                ? "Loading..."
                : `Showing ${filteredData.length.toLocaleString()} candidates`}
            </span>
            <ExportButton
              data={filteredData}
              metrics={filters.metrics}
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
                <RaceTable data={filteredData} metrics={filters.metrics} />
              </div>
            </div>
          ) : (
            <div className="p-6">
              <RaceChart data={filteredData} metrics={filters.metrics} />
            </div>
          )}
        </div>
      </section>
    </section>
  );
}
