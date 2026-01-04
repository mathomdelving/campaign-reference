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
import { useToast } from "@/contexts/ToastContext";
import { supabase } from "@/lib/supabaseClient";
import { getChartColor } from "@/lib/chartTheme";
import { sortQuarterLabels, getDisplayLabel } from "@/utils/quarters";

export function DistrictView() {
  const [cycle, setCycle] = useState<number>(2026);
  const [state, setState] = useState<string>("all");
  const [chamber, setChamber] = useState<ChamberFilter>("H");
  const [district, setDistrict] = useState<string>("all");
  const [selectedParties, setSelectedParties] = useState<string[]>([
    "democrat",
    "republican",
    "other",
  ]);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([
    "totalRaised",
  ]);
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([]);
  const [watchingAll, setWatchingAll] = useState(false);

  const { user } = useAuth();
  const { showToast } = useToast();

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
      const isDem = normalized.includes("dem");
      const isGop = normalized.includes("rep") || normalized.includes("gop");
      if (isDem) return selectedParties.includes("democrat");
      if (isGop) return selectedParties.includes("republican");
      return selectedParties.includes("other");
    });
  }, [selectedParties, candidates]);

  // Convert selected metrics to toggles format
  const metricsFilter = useMemo(() => ({
    totalRaised: selectedMetrics.includes("totalRaised"),
    totalDisbursed: selectedMetrics.includes("totalDisbursed"),
    cashOnHand: selectedMetrics.includes("cashOnHand"),
  }), [selectedMetrics]);

  const primaryMetric = metricsFilter.totalRaised
    ? "totalRaised"
    : metricsFilter.totalDisbursed
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

  const chartMetric = metricsFilter.totalRaised
    ? "receipts"
    : metricsFilter.totalDisbursed
    ? "disbursements"
    : "cashEnding";

  const { chartData, seriesConfig, quarterlyTicks } = useMemo(() => {
    const seriesMap = new Map<string, ChartDatum & { sortKey: string; timestamp: number; coverageEnd: string }>();

    for (const record of quarterlyData) {
      if (!activeCandidateIds.includes(record.candidateId)) continue;
      if (!record.quarterLabel) continue;

      // Derive coverageEnd from quarterLabel if missing (for special filings)
      let coverageEnd = record.coverageEnd;
      if (!coverageEnd && record.quarterLabel) {
        // Extract date from quarterLabel like "PRE-GENERAL Q4 2022.10.19"
        const dateMatch = record.quarterLabel.match(/(\d{4})\.(\d{2})\.(\d{2})/);
        if (dateMatch) {
          const [, year, month, day] = dateMatch;
          coverageEnd = `${year}-${month}-${day}`;
        } else {
          // Fall back to quarter end date
          const quarterMatch = record.quarterLabel.match(/Q([1-4])\s+(\d{4})/);
          if (quarterMatch) {
            const quarter = parseInt(quarterMatch[1]);
            const year = parseInt(quarterMatch[2]);
            const month = quarter * 3;
            const lastDay = new Date(year, month, 0).getDate();
            coverageEnd = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
          }
        }
      }

      if (!coverageEnd) continue; // Skip if we still can't determine date

      // Use quarterLabel + coverageEnd to ensure uniqueness for multiple filings in same quarter
      const key = `${record.quarterLabel}-${coverageEnd}`;
      if (!seriesMap.has(key)) {
        // Convert coverageEnd to timestamp for numeric X-axis
        const timestamp = new Date(coverageEnd).getTime();

        seriesMap.set(key, {
          quarter: getDisplayLabel(record.quarterLabel),  // Clean label for tooltip
          sortKey: record.quarterLabel,  // Full label for sorting
          timestamp,  // Timestamp for X-axis positioning
          coverageEnd: coverageEnd  // Keep for reference
        });
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
      a.timestamp - b.timestamp
    );

    // Trim leading empty quarters - find first quarter with any non-zero data
    let firstNonEmptyIndex = 0;
    for (let i = 0; i < sorted.length; i++) {
      const quarter = sorted[i];
      const hasData = activeCandidateIds.some((candidateId) => {
        const value = quarter[candidateId];
        return typeof value === "number" && value > 0;
      });
      if (hasData) {
        firstNonEmptyIndex = i;
        break;
      }
    }

    const trimmed = sorted.slice(firstNonEmptyIndex);

    // Extract unique quarters for tick calculation
    const quarterSet = new Set<string>();
    trimmed.forEach((datum) => {
      const match = datum.sortKey.match(/Q([1-4])\s+(\d{4})/);
      if (match) {
        quarterSet.add(`Q${match[1]} ${match[2]}`);
      }
    });

    const sortedQuarters = Array.from(quarterSet).sort((a, b) => sortQuarterLabels(a, b));

    // Calculate quarterly tick timestamps (Q1=Mar 31, Q2=Jun 30, Q3=Sep 30, Q4=Dec 31)
    const quarterlyTicks = sortedQuarters.map(q => {
      const match = q.match(/Q([1-4])\s+(\d{4})/);
      if (!match) return { label: q, timestamp: 0 };

      const quarter = parseInt(match[1]);
      const year = parseInt(match[2]);

      // Quarter end dates: Q1=March 31, Q2=June 30, Q3=Sept 30, Q4=Dec 31
      const month = quarter * 3 - 1; // 2, 5, 8, 11 (0-indexed)
      const lastDay = new Date(year, month + 1, 0).getDate(); // Get last day of month

      return {
        label: q,
        timestamp: new Date(year, month, lastDay).getTime()
      };
    });

    // If more than 12 quarters, show only Q1 and Q3
    const displayTicks = quarterlyTicks.length > 12
      ? quarterlyTicks.filter(t => t.label.match(/Q[13]\s+\d{4}/))
      : quarterlyTicks;

    const config: ChartSeriesConfig[] = activeCandidateIds.map((candidateId, index) => {
      const candidate = sortedCandidates.find((item) => item.candidate_id === candidateId);
      return {
        key: candidateId,
        label: candidate?.name ?? candidateId,
        color: getChartColor(index),
        strokeWidth: candidateId === activeCandidateIds[0] ? 2.5 : 1.5,
      };
    });

    return {
      chartData: trimmed.map(({ sortKey, coverageEnd, ...datum }) => datum),
      seriesConfig: config,
      quarterlyTicks: displayTicks
    };
  }, [quarterlyData, activeCandidateIds, chartMetric, sortedCandidates]);

  const handleCandidateToggle = (candidateId: string) => {
    setSelectedCandidates((prev) =>
      prev.includes(candidateId)
        ? prev.filter((id) => id !== candidateId)
        : [...prev, candidateId]
    );
  };

  const handleCycleChange = (value: number) => {
    setCycle(value);
    setSelectedCandidates([]);
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

  const summaryLabel = [
    state === "all" ? "Nationwide" : state,
    chamber === "H" ? "House" : "Senate",
    district !== "all" ? district : null,
  ]
    .filter(Boolean)
    .join(" / ");

  const handleResetFilters = () => {
    setCycle(2026);
    setState("all");
    setChamber("H");
    setDistrict("all");
    setSelectedMetrics(["totalRaised"]);
    setSelectedParties(["democrat", "republican", "other"]);
    setSelectedCandidates([]);
  };

  const handleWatchAll = async () => {
    if (!user) {
      showToast("Please sign in to watch candidates.", "info");
      return;
    }

    if (sortedCandidates.length === 0) {
      showToast("No candidates available to watch for the current selection.", "info");
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
        showToast("You have reached the maximum of 50 followed candidates.", "warning");
        setWatchingAll(false);
        return;
      }

      const candidatesToWatch = sortedCandidates
        .filter((candidate) => !existingIds.has(candidate.candidate_id))
        .slice(0, remainingSlots);

      if (candidatesToWatch.length === 0) {
        showToast("You are already watching these candidates.", "info");
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

      showToast(`Successfully watching ${candidatesToWatch.length} candidates.`, "success");
    } catch (err) {
      console.error("Error following candidates in bulk:", err);
      showToast("Failed to watch all candidates. Please try again.", "error");
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
        cycle={cycle}
        state={state}
        chamber={chamber}
        district={district}
        selectedParties={selectedParties}
        selectedMetrics={selectedMetrics}
        districts={districts}
        onCycleChange={handleCycleChange}
        onStateChange={handleStateChange}
        onChamberChange={handleChamberChange}
        onDistrictChange={handleDistrictChange}
        onPartiesChange={setSelectedParties}
        onMetricsChange={setSelectedMetrics}
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
                  metrics={metricsFilter}
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
              quarterlyTicks={quarterlyTicks}
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
