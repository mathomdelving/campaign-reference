'use client';

import type { ChamberFilter, MetricToggles } from "@/hooks/useFilters";
import type { DistrictOption } from "@/hooks/useDistrictOptions";

const STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
];

interface PartySelection {
  democrat: boolean;
  republican: boolean;
  other: boolean;
}

interface DistrictFiltersProps {
  state: string;
  chamber: ChamberFilter;
  district: string;
  metrics: MetricToggles;
  partySelection: PartySelection;
  districts: DistrictOption[];
  onStateChange: (state: string) => void;
  onChamberChange: (value: ChamberFilter) => void;
  onDistrictChange: (district: string) => void;
  onMetricToggle: (metric: keyof MetricToggles, value: boolean) => void;
  onPartyToggle: (key: keyof PartySelection) => void;
  summaryLabel: string;
  onReset: () => void;
}

export function DistrictFilters({
  state,
  chamber,
  district,
  metrics,
  partySelection,
  districts,
  onStateChange,
  onChamberChange,
  onDistrictChange,
  onMetricToggle,
  onPartyToggle,
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

      <div className="mt-4 flex flex-wrap items-start gap-4">
        <div className="flex flex-col gap-2" style={{ width: "140px" }}>
          <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
            State
          </label>
          <select
            value={state}
            onChange={(event) => onStateChange(event.target.value)}
            className="h-[42px] border border-gray-300 bg-white px-4 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
          >
            <option value="all">All States</option>
            {STATES.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-2" style={{ width: "240px" }}>
          <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
            Chamber
          </label>
          <div className="flex h-[42px] gap-2">
            {(
              [
                { value: "H" as ChamberFilter, label: "House" },
                { value: "S" as ChamberFilter, label: "Senate" },
              ] satisfies Array<{ value: ChamberFilter; label: string }>
            ).map((option) => {
              const active = chamber === option.value;
                return (
                  <button
                    key={option.value}
                    onClick={() => onChamberChange(option.value)}
                    className={[
                      "flex-1 border border-gray-300 bg-white px-3 text-sm font-medium transition",
                      active
                        ? "bg-rb-gold text-rb-brand-navy border-rb-gold"
                        : "text-gray-600 hover:border-rb-brand-navy hover:text-rb-brand-navy",
                    ].join(" ")}
                  >
                    {option.label}
                  </button>
                );
            })}
          </div>
        </div>

        <div className="flex flex-col gap-2" style={{ width: "180px" }}>
          <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
            {chamber === "H" ? "District" : "Seat"}
          </label>
          <select
            value={district}
            onChange={(event) => onDistrictChange(event.target.value)}
            disabled={state === "all"}
            className="h-[42px] border border-gray-300 bg-white px-4 text-sm font-medium text-gray-900 focus:border-rb-brand-navy focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
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
        </div>

        <div className="flex flex-col gap-2" style={{ width: "220px" }}>
          <label className="text-xs font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
            Party Filter
          </label>
          <div className="flex h-[42px] gap-2">
            {([
              { key: "democrat", label: "DEM" },
              { key: "republican", label: "GOP" },
              { key: "other", label: "Other" },
            ] satisfies Array<{ key: keyof PartySelection; label: string }>).map(
              (entry) => {
                const active = partySelection[entry.key];
                return (
                  <button
                    key={entry.key}
                    onClick={() => onPartyToggle(entry.key)}
                    className={[
                      "flex-1 border border-gray-300 px-3 text-sm font-medium transition",
                      active
                        ? "bg-rb-gold text-rb-brand-navy border-rb-gold"
                        : "bg-white text-gray-600 hover:border-rb-brand-navy hover:text-rb-brand-navy",
                    ].join(" ")}
                  >
                    {entry.label}
                  </button>
                );
              }
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {(
          [
            ["totalRaised", "Total Raised"],
            ["totalDisbursed", "Total Spent"],
            ["cashOnHand", "Cash on Hand"],
          ] satisfies Array<[keyof MetricToggles, string]>
        ).map(([key, label]) => {
          const active = metrics[key];
          return (
            <button
              key={key}
              onClick={() => onMetricToggle(key, !active)}
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
  );
}
