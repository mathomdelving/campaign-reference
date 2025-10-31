'use client';

import { useEffect, useMemo, useState } from "react";
import { DistrictFilters } from "@/components/district/DistrictFilters";
import { CandidateGrid } from "@/components/district/CandidateGrid";
import { useDistrictOptions } from "@/hooks/useDistrictOptions";
import { useDistrictCandidates } from "@/hooks/useDistrictCandidates";
import { useQuarterlyData } from "@/hooks/useQuarterlyData";
import type { ChamberFilter, MetricToggles } from "@/hooks/useFilters";
import { CRLineChart } from "@/components/CRLineChart";
import { getPartyColor } from "@/utils/formatters";
import type { ChartDatum, ChartSeriesConfig } from "@/components/CRLineChart";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabaseClient";

const DEFAULT_METRICS: MetricToggles = {
  totalRaised: true,
  totalDisbursed: false,
  cashOnHand: false,
};

const DEFAULT_PARTY_FILTER = {
  democrat: true,
  republican: true,
  other: true,
};

export function DistrictView() {
  const [state, setState] = useState<string>("all");
  const [chamber, setChamber] = useState<ChamberFilter>("H");
  const [district, setDistrict] = useState<string>("all");
  const [metrics, setMetrics] = useState<MetricToggles>({ ...DEFAULT_METRICS });
  const [partyFilter, setPartyFilter] = useState<{ democrat: boolean; republican: boolean; other: boolean }>(() => ({
    ...DEFAULT_PARTY_FILTER,
  }));
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([]);
  const [watchingAll, setWatchingAll] = useState(false);

  const cycle = 2026;
  const { user } = useAuth();

  const { districts } = useDistrictOptions(state, chamber, cycle);
  const {
    data: candidates,
    loading,
    error,
    lastUpdated,
  } = useDistrictCandidates({
    state,
    chamber,
    district,
    cycle,
  });

  const filteredCandidates = useMemo(() => {
    return candidates.filter((candidate) => {
      const normalized = (candidate.party ?? "").toLowerCase();
      const isDem = normalized.includes("democrat");
      const isGop = normalized.includes("republican");
      if (isDem) return partyFilter.democrat;
      if (isGop) return partyFilter.republican;
      return partyFilter.other;
    });
  }, [partyFilter, candidates]);

  const primaryMetric = metrics.totalRaised
    ? "totalRaised"
    : metrics.totalDisbursed
    ? "totalDisbursed"
    : "cashOnHand";

  const sortedCandidates = useMemo(() => {
    return [...filteredCandidates].sort(
      (a, b) => (b[primaryMetric] ?? 0) - (a[primaryMetric] ?? 0)
    );
  }, [filteredCandidates, primaryMetric]);

  useEffect(() => {
    if (sortedCandidates.length === 0) {
      setSelectedCandidates([]);
      return;
    }

    setSelectedCandidates((prev) =>
      prev.filter((id) =>
        sortedCandidates.some((candidate) => candidate.candidate_id === id)
      )
    );
  }, [sortedCandidates]);

  const activeCandidateIds = useMemo(() => {
    if (selectedCandidates.length === 0) return [];

    return selectedCandidates.filter((id) =>
      sortedCandidates.some((candidate) => candidate.candidate_id === id)
    );
  }, [selectedCandidates, sortedCandidates]);

  const { data: quarterlyData, loading: quarterlyLoading } = useQuarterlyData(
    activeCandidateIds,
    cycle
  );

  const chartMetric = metrics.totalRaised
    ? "receipts"
    : metrics.totalDisbursed
    ? "disbursements"
    : "cashEnding";

  const { chartData, seriesConfig } = useMemo(() => {
    const seriesMap = new Map<string, ChartDatum>();

    for (const record of quarterlyData) {
      if (!activeCandidateIds.includes(record.candidateId)) continue;
      if (!record.quarterLabel) continue;

      const key = record.quarterLabel;
      if (!seriesMap.has(key)) {
        seriesMap.set(key, { quarter: key });
      }

      const datum = seriesMap.get(key)!;
      datum[record.candidateId] =
        chartMetric === "receipts"
          ? record.receipts
          : chartMetric === "disbursements"
          ? record.disbursements
          : record.cashEnding;
    }

    const sorted = Array.from(seriesMap.values()).sort((a, b) =>
      a.quarter.localeCompare(b.quarter)
    );

    const config: ChartSeriesConfig[] = activeCandidateIds.map((candidateId) => {
      const candidate = sortedCandidates.find((item) => item.candidate_id === candidateId);
      return {
        key: candidateId,
        label: candidate?.name ?? candidateId,
        color: getPartyColor(candidate?.party ?? null),
        strokeWidth: candidateId === activeCandidateIds[0] ? 2.5 : 1.5,
      };
    });

    return { chartData: sorted, seriesConfig: config };
  }, [quarterlyData, activeCandidateIds, chartMetric, sortedCandidates]);

  const handleCandidateToggle = (candidateId: string) => {
    setSelectedCandidates((prev) =>
      prev.includes(candidateId)
        ? prev.filter((id) => id !== candidateId)
        : [...prev, candidateId]
    );
  };

  const handleStateChange = (value: string) => {
    setState(value);
    setDistrict("all");
    setSelectedCandidates([]);
  };

  const handleChamberChange = (value: ChamberFilter) => {
    setChamber(value);
    setDistrict("all");
    setSelectedCandidates([]);
  };

  const handleDistrictChange = (value: string) => {
    setDistrict(value);
    setSelectedCandidates([]);
  };

  const handleMetricToggle = (metric: keyof MetricToggles, value: boolean) => {
    setMetrics((prev) => ({
      ...prev,
      [metric]: value,
    }));
  };

  const summaryLabel = [
    state === "all" ? "Nationwide" : state,
    chamber === "H" ? "House" : "Senate",
    district !== "all" ? district : null,
  ]
    .filter(Boolean)
    .join(" / ");

  const handleResetFilters = () => {
    setState("all");
    setChamber("H");
    setDistrict("all");
    setMetrics({ ...DEFAULT_METRICS });
    setPartyFilter({ ...DEFAULT_PARTY_FILTER });
    setSelectedCandidates([]);
  };

  const handleWatchAll = async () => {
    if (!user) {
      alert("Please sign in to watch candidates.");
      return;
    }

    if (sortedCandidates.length === 0) {
      alert("No candidates available to watch for the current selection.");
      return;
    }

    setWatchingAll(true);

    try {
      const { data: existingFollows, error: existingError } = await supabase
        .from("user_candidate_follows")
        .select("candidate_id")
        .eq("user_id", user.id);

      if (existingError) throw existingError;

      const existingIds = new Set(
        existingFollows?.map((item) => item.candidate_id) ?? []
      );
      const currentCount = existingIds.size;
      const remainingSlots = 50 - currentCount;

      if (remainingSlots <= 0) {
        alert("You have reached the maximum of 50 followed candidates.");
        setWatchingAll(false);
        return;
      }

      const candidatesToWatch = sortedCandidates
        .filter((candidate) => !existingIds.has(candidate.candidate_id))
        .slice(0, remainingSlots);

      if (candidatesToWatch.length === 0) {
        alert("You are already watching these candidates.");
        setWatchingAll(false);
        return;
      }

      if (
        candidatesToWatch.length <
        sortedCandidates.filter(
          (candidate) => !existingIds.has(candidate.candidate_id)
        ).length
      ) {
        const proceed = confirm(
          `You can watch ${candidatesToWatch.length} additional candidates before hitting the 50 candidate limit. Continue?`
        );
        if (!proceed) {
          setWatchingAll(false);
          return;
        }
      }

      const payload = candidatesToWatch.map((candidate) => ({
        user_id: user.id,
        candidate_id: candidate.candidate_id,
        candidate_name: candidate.name,
        party: candidate.party,
        office: candidate.office,
        state: candidate.state,
        district: candidate.district,
        notification_enabled: true,
      }));

      const { error } = await supabase
        .from("user_candidate_follows")
        .upsert(payload, { onConflict: "user_id,candidate_id" });

      if (error) throw error;

      alert(`Successfully watching ${candidatesToWatch.length} candidates.`);
    } catch (err) {
      console.error("Error following candidates in bulk:", err);
      alert("Failed to watch all candidates. Please try again.");
    } finally {
      setWatchingAll(false);
    }
  };

  const showChart =
    state !== "all" && chartData.length > 0 && activeCandidateIds.length > 0;

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="font-display text-3xl font-semibold text-gray-900">
          Search by District
        </h1>
        <p className="text-sm text-gray-600">
          Select two or more candidates to compare quarterly results in the chart below.
        </p>
      </header>

      <DistrictFilters
        state={state}
        chamber={chamber}
        district={district}
        metrics={metrics}
        partySelection={partyFilter}
        districts={districts}
        onStateChange={handleStateChange}
        onChamberChange={handleChamberChange}
        onDistrictChange={handleDistrictChange}
        onMetricToggle={handleMetricToggle}
        onPartyToggle={(key) =>
          setPartyFilter((prev) => ({
            ...prev,
            [key]: !prev[key],
          }))
        }
        summaryLabel={summaryLabel}
        onReset={handleResetFilters}
      />

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 text-sm uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
          <span>
            {loading
              ? "Fetching candidates…"
              : `${sortedCandidates.length.toLocaleString()} candidates`}
          </span>
          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span className="tracking-[0.1rem] sm:tracking-[0.2rem]">
                Updated {new Date(lastUpdated).toLocaleDateString()}
              </span>
            )}
            <button
              onClick={handleWatchAll}
              disabled={watchingAll || sortedCandidates.length === 0}
              className="inline-flex items-center justify-center rounded-md border border-rb-brand-navy px-4 py-2 text-xs font-semibold uppercase tracking-[0.1rem] sm:tracking-[0.2rem] text-rb-brand-navy transition hover:bg-rb-gold hover:text-rb-brand-navy disabled:cursor-not-allowed disabled:opacity-60"
            >
              {watchingAll ? "Watching..." : "Watch All"}
            </button>
          </div>
        </div>

        <div className="border-2 border-rb-brand-navy bg-white">
          {error ? (
            <div className="p-12 text-center text-sm text-red-600">{error}</div>
          ) : (
            <div className="w-full overflow-x-auto">
              <div className="min-w-[800px]">
                <CandidateGrid
                  candidates={sortedCandidates}
                  selected={activeCandidateIds}
                  onToggle={handleCandidateToggle}
                  metrics={metrics}
                />
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between text-sm uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
          <span>Quarterly Trend — {chartMetricLabel(chartMetric)}</span>
          <span>
            {quarterlyLoading
              ? "Loading quarterly data…"
              : `${activeCandidateIds.length} active series`}
          </span>
        </div>

        {showChart ? (
          <div className="border-2 border-rb-brand-navy bg-white p-6">
            <CRLineChart
              data={chartData}
              series={seriesConfig}
              height={420}
              yAxisFormatter={(value) => formatCurrencyLabel(value)}
            />
          </div>
        ) : (
          <div className="border-2 border-rb-brand-navy bg-white p-12 text-center text-sm text-gray-600">
            Select candidates above to compare timeseries data.
          </div>
        )}
      </section>
    </section>
  );
}

function chartMetricLabel(metric: "receipts" | "disbursements" | "cashEnding") {
  switch (metric) {
    case "receipts":
      return "Total Raised";
    case "disbursements":
      return "Total Spent";
    case "cashEnding":
      return "Cash on Hand";
    default:
      return "Fundraising";
  }
}

function formatCurrencyLabel(value: number) {
  if (!value) return "$0";
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`;
  }
  return `$${Math.round(value)}`;
}
