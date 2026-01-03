'use client';

import type { ChamberFilter, MetricToggles } from "@/hooks/useFilters";
import type { DistrictOption } from "@/hooks/useDistrictOptions";
import { MultiSelect, type MultiSelectOption } from "@/components/shared/MultiSelect";

const STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
];

const CYCLES = [2026, 2024, 2022, 2020];

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

interface DistrictFiltersProps {
  cycle: number;
  state: string;
  chamber: ChamberFilter;
  district: string;
  selectedParties: string[];
  selectedMetrics: string[];
  districts: DistrictOption[];
  onCycleChange: (cycle: number) => void;
  onStateChange: (state: string) => void;
  onChamberChange: (value: ChamberFilter) => void;
  onDistrictChange: (district: string) => void;
  onPartiesChange: (parties: string[]) => void;
  onMetricsChange: (metrics: string[]) => void;
  summaryLabel: string;
  onReset: () => void;
}

export function DistrictFilters({
  cycle,
  state,
  chamber,
  district,
  selectedParties,
  selectedMetrics,
  districts,
  onCycleChange,
  onStateChange,
  onChamberChange,
  onDistrictChange,
  onPartiesChange,
  onMetricsChange,
  summaryLabel,
  onReset,
}: DistrictFiltersProps) {
  return (
    <section className="border-2 border-rb-brand-navy bg-white p-6 text-gray-900">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <span className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
          {summaryLabel}
        </span>
        <button
          onClick={onReset}
          className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.25rem] text-gray-600 transition hover:text-rb-brand-navy"
        >
          Reset All
        </button>
      </div>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 items-start">
        <div className="flex flex-col gap-2 w-full sm:w-[140px]">
          <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
            Cycle
          </label>
          <div className="relative">
            <select
              value={cycle}
              onChange={(event) => onCycleChange(Number(event.target.value))}
              className="h-[42px] w-full appearance-none border border-gray-300 bg-white px-4 pr-10 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none"
            >
              {CYCLES.map((c) => (
                <option key={c} value={c}>
                  {c}
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
              value={chamber}
              onChange={(event) => onChamberChange(event.target.value as ChamberFilter)}
              className="h-[42px] w-full appearance-none border border-gray-300 bg-white px-4 pr-10 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none"
            >
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
              value={state}
              onChange={(event) => onStateChange(event.target.value)}
              className="h-[42px] w-full appearance-none border border-gray-300 bg-white px-4 pr-10 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
            >
              <option value="all">All States</option>
              {STATES.map((code) => (
                <option key={code} value={code}>
                  {code}
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
            {chamber === "H" ? "District" : "Seat"}
          </label>
          <div className="relative">
            <select
              value={district}
              onChange={(event) => onDistrictChange(event.target.value)}
              disabled={state === "all"}
              className="h-[42px] w-full appearance-none border border-gray-300 bg-white px-4 pr-10 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
            >
              <option value="all">
                {chamber === "H" ? "All Districts" : "All Seats"}
              </option>
              {districts.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
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
            onChange={onPartiesChange}
            placeholder="Select parties"
          />
        </div>

        <div className="w-full sm:max-w-[200px]">
          <MultiSelect
            label="Metrics"
            options={METRIC_OPTIONS}
            selected={selectedMetrics}
            onChange={onMetricsChange}
            placeholder="Select metrics"
          />
        </div>
      </div>
    </section>
  );
}
