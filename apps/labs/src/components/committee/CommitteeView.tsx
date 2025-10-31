'use client';

import { useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { CRLineChart } from "@/components/CRLineChart";
import type { ChartDatum, ChartSeriesConfig } from "@/components/CRLineChart";
import { useQuarterlyData } from "@/hooks/useQuarterlyData";
import { useCommitteeQuarterlyData } from "@/hooks/useCommitteeQuarterlyData";
import { getPartyColor, formatCurrency } from "@/utils/formatters";
import { FollowButton } from "@/components/follow/FollowButton";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  throw new Error(
    "Supabase credentials are missing. Check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY."
  );
}

const browserClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: { persistSession: false },
});

const METRIC_OPTIONS = [
  { value: "receipts", label: "Total Raised" },
  { value: "disbursements", label: "Total Spent" },
  { value: "cashEnding", label: "Cash on Hand" },
] as const;

type MetricValue = typeof METRIC_OPTIONS[number]["value"];

type EntityType = "candidate" | "committee";

type EntitySelection = {
  type: EntityType;
  id: string;
  label: string;
  party?: string | null;
  color?: string;
};

type EntityResult = EntitySelection & { subtitle?: string };

const QUICK_COMMITTEES: EntitySelection[] = [
  { type: "committee", id: "C00000935", label: "DCCC", color: "#5B8AEF" },
  { type: "committee", id: "C00042366", label: "DSCC", color: "#3366CC" },
  { type: "committee", id: "C00075820", label: "NRCC", color: "#E06A6A" },
  { type: "committee", id: "C00027466", label: "NRSC", color: "#C44D4D" },
];

function entityKey(entity: EntitySelection) {
  return `${entity.type}-${entity.id}`;
}

export function CommitteeView() {
  const [metric, setMetric] = useState<MetricValue>("receipts");
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<EntityResult[]>([]);
  const [selectedEntities, setSelectedEntities] = useState<EntitySelection[]>([]);
  const cycle = 2026;

  const candidateIds = useMemo(
    () => selectedEntities.filter((entity) => entity.type === "candidate").map((entity) => entity.id),
    [selectedEntities]
  );
  const committeeIds = useMemo(
    () => selectedEntities.filter((entity) => entity.type === "committee").map((entity) => entity.id),
    [selectedEntities]
  );

  const { data: candidateQuarterlies } = useQuarterlyData(candidateIds, cycle);
  const { data: committeeQuarterlies } = useCommitteeQuarterlyData(committeeIds, cycle);

  const chartData = useMemo<ChartDatum[]>(() => {
    const map = new Map<string, ChartDatum>();

    for (const record of candidateQuarterlies) {
      if (!record.quarterLabel || !candidateIds.includes(record.candidateId)) continue;
      const key = record.quarterLabel;
      if (!map.has(key)) map.set(key, { quarter: key });
      const datum = map.get(key)!;
      datum[record.candidateId] =
        metric === "receipts"
          ? record.receipts
          : metric === "disbursements"
          ? record.disbursements
          : record.cashEnding;
    }

    for (const record of committeeQuarterlies) {
      if (!record.quarterLabel || !committeeIds.includes(record.committeeId)) continue;
      const key = record.quarterLabel;
      if (!map.has(key)) map.set(key, { quarter: key });
      const datum = map.get(key)!;
      datum[record.committeeId] =
        metric === "receipts"
          ? record.receipts
          : metric === "disbursements"
          ? record.disbursements
          : record.cashEnding;
    }

    return Array.from(map.values()).sort((a, b) => a.quarter.localeCompare(b.quarter));
  }, [candidateQuarterlies, committeeQuarterlies, metric, candidateIds, committeeIds]);

  const seriesConfig = useMemo<ChartSeriesConfig[]>(() => {
    return selectedEntities.map((entity) => ({
      key: entity.id,
      label: entity.label,
      color:
        entity.type === "committee"
          ? entity.color ?? "#FFC906"
          : getPartyColor(entity.party ?? null),
      strokeWidth: 2,
    }));
  }, [selectedEntities]);

  const summaries = useMemo(() => {
    const latestById = new Map<
      string,
      { id: string; label: string; type: EntityType; party?: string | null; value: number; coverage?: string | null }
    >();

    candidateIds.forEach((candidateId) => {
      const entity = selectedEntities.find((item) => item.id === candidateId && item.type === "candidate");
      if (!entity) return;
      const records = candidateQuarterlies.filter((row) => row.candidateId === candidateId);
      if (records.length === 0) return;
      const latest = records.reduce((acc, current) =>
        !acc.coverageEnd || (current.coverageEnd && current.coverageEnd > acc.coverageEnd) ? current : acc
      );
      const value = metric === "receipts" ? latest.receipts : metric === "disbursements" ? latest.disbursements : latest.cashEnding;
      latestById.set(candidateId, {
        id: candidateId,
        label: entity.label,
        type: "candidate",
        party: entity.party ?? null,
        value,
        coverage: latest.coverageEnd,
      });
    });

    committeeIds.forEach((committeeId) => {
      const entity = selectedEntities.find((item) => item.id === committeeId && item.type === "committee");
      if (!entity) return;
      const records = committeeQuarterlies.filter((row) => row.committeeId === committeeId);
      if (records.length === 0) return;
      const latest = records.reduce((acc, current) =>
        !acc.coverageEnd || (current.coverageEnd && current.coverageEnd > acc.coverageEnd) ? current : acc
      );
      const value = metric === "receipts" ? latest.receipts : metric === "disbursements" ? latest.disbursements : latest.cashEnding;
      latestById.set(committeeId, {
        id: committeeId,
        label: entity.label,
        type: "committee",
        value,
        coverage: latest.coverageEnd,
      });
    });

    return Array.from(latestById.values());
  }, [selectedEntities, metric, candidateQuarterlies, committeeQuarterlies, candidateIds, committeeIds]);

  useEffect(() => {
    if (searchTerm.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const { data, error } = await browserClient
          .from("candidates")
          .select("candidate_id, name, party")
          .ilike("name", `%${searchTerm}%`)
          .limit(8);

        if (error) throw error;

        const candidateResults: EntityResult[] =
          data?.map((row) => ({
            type: "candidate" as const,
            id: row.candidate_id,
            label: row.name,
            party: row.party,
            subtitle: row.party ?? undefined,
          })) ?? [];

        const committeeMatches = QUICK_COMMITTEES.filter((entity) =>
          entity.label.toLowerCase().includes(searchTerm.toLowerCase())
        ).map((entity) => ({ ...entity, subtitle: "Committee" }));

        if (!cancelled) {
          setSearchResults([...committeeMatches, ...candidateResults]);
        }
      } catch (error) {
        console.error("Search failed", error);
        if (!cancelled) setSearchResults([]);
      } finally {
        // no-op
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [searchTerm]);

  const handleSelectEntity = (entity: EntitySelection) => {
    setSelectedEntities((prev) => {
      const exists = prev.some((item) => entityKey(item) === entityKey(entity));
      if (exists) return prev;
      return [...prev, entity];
    });
    setSearchTerm("");
    setSearchResults([]);
  };

  const handleRemoveEntity = (entity: EntitySelection) => {
    setSelectedEntities((prev) => prev.filter((item) => entityKey(item) !== entityKey(entity)));
  };

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="font-display text-3xl font-semibold text-gray-900">Search by Candidate and Committee.</h1>
        <p className="text-sm text-gray-600">
          Select two or more candidates / committees to compare results in the chart below.
        </p>
      </header>

      <section className="border-2 border-rb-brand-navy bg-white p-6 space-y-6 text-gray-900">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-sm font-semibold uppercase tracking-[0.3rem] text-gray-600">Metric</h2>
          <div className="flex border border-gray-300 bg-white p-1">
            {METRIC_OPTIONS.map((option) => {
              const active = metric === option.value;
              return (
                <button
                  key={option.value}
                  onClick={() => setMetric(option.value)}
                  className={`px-4 py-2 text-xs font-semibold uppercase tracking-[0.2rem] transition ${
                    active
                      ? "bg-rb-gold text-rb-brand-navy"
                      : "text-gray-600 hover:text-rb-brand-navy"
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 min-w-[260px]">
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search candidates or committees"
              className="w-full border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-rb-brand-navy focus:outline-none"
            />
            {searchTerm && searchResults.length > 0 && (
              <div className="absolute z-20 mt-2 w-full overflow-hidden border-2 border-rb-brand-navy bg-white shadow-lg">
                {searchResults.map((result) => (
                  <button
                    key={`${result.type}-${result.id}`}
                    onClick={() =>
                      handleSelectEntity({
                        type: result.type,
                        id: result.id,
                        label: result.label,
                        party: result.party,
                        color: result.color,
                      })
                    }
                    className="flex w-full flex-col items-start gap-1 px-4 py-3 text-left text-sm text-gray-900 transition hover:bg-gray-100"
                  >
                    <span>{result.label}</span>
                    {result.subtitle && (
                      <span className="text-xs uppercase tracking-[0.25rem] text-gray-600">
                        {result.subtitle}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2" />
        </div>

        <div className="flex flex-wrap gap-2">
          {selectedEntities.map((entity) => (
            <button
              key={entityKey(entity)}
              onClick={() => handleRemoveEntity(entity)}
              className="inline-flex items-center gap-2 border border-gray-300 bg-white px-3 py-2 text-xs uppercase tracking-[0.2rem] text-rb-brand-navy transition hover:bg-gray-100"
            >
              <span>{entity.label}</span>
              <span className="text-gray-400">×</span>
            </button>
          ))}
        </div>
      </section>

      <section className="border-2 border-rb-brand-navy bg-white">
        <div className="flex items-center justify-between border-b border-gray-200 p-6 text-sm uppercase tracking-[0.3rem] text-gray-600">
          <span>Quarterly Trend — {METRIC_OPTIONS.find((option) => option.value === metric)?.label}</span>
          <span>{selectedEntities.length} entities</span>
        </div>

        {chartData.length === 0 ? (
          <div className="p-12 text-center text-sm text-gray-600">
            Add at least one candidate or committee to render the chart.
          </div>
        ) : (
          <div className="p-6">
            <CRLineChart
              data={chartData}
              series={seriesConfig}
              height={420}
              yAxisFormatter={formatCurrencyLabel}
            />
          </div>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-[0.3rem] text-gray-600">
          Latest Filing Snapshot
        </h2>
        <div className="grid gap-4 lg:grid-cols-3">
          {summaries.length === 0 ? (
            <div className="border-2 border-rb-brand-navy bg-white p-8 text-center text-sm text-gray-600">
              Select entities to view filing snapshots.
            </div>
          ) : (
            summaries.map((summary) => (
              <div
                key={`${summary.type}-${summary.id}`}
                className="border-2 border-rb-brand-navy bg-white p-5 text-gray-900"
              >
                <div className="flex items-start justify-between">
                  <div className="text-xs uppercase tracking-[0.3rem] text-gray-600">
                    {summary.label}
                  </div>
                  {summary.type === "candidate" && (
                    <FollowButton
                      candidateId={summary.id}
                      candidateName={summary.label}
                      party={summary.party ?? null}
                      office={null}
                      state={null}
                      district={null}
                      size="sm"
                    />
                  )}
                </div>
                <div className="mt-3 font-display text-2xl text-rb-brand-navy">
                  {formatCurrency(summary.value)}
                </div>
                <div className="mt-4 text-[10px] uppercase tracking-[0.3rem] text-gray-600">
                  Updated {summary.coverage ? summary.coverage.slice(0, 10) : "—"}
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </section>
  );
}

function formatCurrencyLabel(value: number) {
  if (!value) return "$0";
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${Math.round(value)}`;
}
