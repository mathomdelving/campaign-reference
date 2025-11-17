'use client';

import { useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { CRLineChart } from "@/components/CRLineChart";
import type { ChartDatum, ChartSeriesConfig } from "@/components/CRLineChart";
import { useQuarterlyData } from "@/hooks/useQuarterlyData";
import { useCommitteeQuarterlyData } from "@/hooks/useCommitteeQuarterlyData";
import { getPartyColor, formatCurrency } from "@/utils/formatters";
import { FollowButton } from "@/components/follow/FollowButton";
import { sortQuarterLabels, getDisplayLabel } from "@/utils/quarters";
import { getChartColor } from "@/lib/chartTheme";

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

// Nickname dictionary for common political names (bidirectional)
const NICKNAME_MAP: Record<string, string[]> = {
  // Mike/Michael
  'mike': ['mike', 'michael'],
  'michael': ['mike', 'michael'],
  // Jim/James/Jimmy
  'jim': ['jim', 'james', 'jimmy'],
  'james': ['jim', 'james', 'jimmy'],
  'jimmy': ['jim', 'james', 'jimmy'],
  // Bob/Robert/Bobby
  'bob': ['bob', 'robert', 'bobby'],
  'robert': ['bob', 'robert', 'bobby'],
  'bobby': ['bob', 'robert', 'bobby'],
  // Bill/William/Billy
  'bill': ['bill', 'william', 'billy'],
  'william': ['bill', 'william', 'billy'],
  'billy': ['bill', 'william', 'billy'],
  // Joe/Joseph
  'joe': ['joe', 'joseph'],
  'joseph': ['joe', 'joseph'],
  // Tom/Thomas
  'tom': ['tom', 'thomas'],
  'thomas': ['tom', 'thomas'],
  // Dick/Richard/Rick/Ricky
  'dick': ['dick', 'richard', 'rick', 'ricky'],
  'richard': ['dick', 'richard', 'rick', 'ricky'],
  'rick': ['dick', 'richard', 'rick', 'ricky'],
  'ricky': ['dick', 'richard', 'rick', 'ricky'],
  // Jack/John/Johnny
  'jack': ['jack', 'john', 'johnny'],
  'john': ['jack', 'john', 'johnny'],
  'johnny': ['jack', 'john', 'johnny'],
  // Ben/Benjamin
  'ben': ['ben', 'benjamin'],
  'benjamin': ['ben', 'benjamin'],
  // Dan/Daniel/Danny
  'dan': ['dan', 'daniel', 'danny'],
  'daniel': ['dan', 'daniel', 'danny'],
  'danny': ['dan', 'daniel', 'danny'],
  // Chris/Christopher
  'chris': ['chris', 'christopher'],
  'christopher': ['chris', 'christopher'],
  // Matt/Matthew
  'matt': ['matt', 'matthew'],
  'matthew': ['matt', 'matthew'],
  // Dave/David
  'dave': ['dave', 'david'],
  'david': ['dave', 'david'],
  // Steve/Steven/Stephen
  'steve': ['steve', 'steven', 'stephen'],
  'steven': ['steve', 'steven', 'stephen'],
  'stephen': ['steve', 'steven', 'stephen'],
  // Tony/Anthony
  'tony': ['tony', 'anthony'],
  'anthony': ['tony', 'anthony'],
  // Chuck/Charles/Charlie
  'chuck': ['chuck', 'charles', 'charlie'],
  'charles': ['chuck', 'charles', 'charlie'],
  'charlie': ['chuck', 'charles', 'charlie'],
  // Ed/Edward/Eddie
  'ed': ['ed', 'edward', 'eddie'],
  'edward': ['ed', 'edward', 'eddie'],
  'eddie': ['ed', 'edward', 'eddie'],
  // Pete/Peter
  'pete': ['pete', 'peter'],
  'peter': ['pete', 'peter'],
  // Pat/Patricia/Patrick
  'pat': ['pat', 'patricia', 'patrick'],
  'patricia': ['pat', 'patricia'],
  'patrick': ['pat', 'patrick'],
  // Liz/Elizabeth/Beth
  'liz': ['liz', 'elizabeth', 'beth', 'betty'],
  'elizabeth': ['liz', 'elizabeth', 'beth', 'betty'],
  'beth': ['liz', 'elizabeth', 'beth', 'betty'],
  'betty': ['liz', 'elizabeth', 'beth', 'betty'],
  // Debbie/Deborah
  'debbie': ['debbie', 'deborah'],
  'deborah': ['debbie', 'deborah'],
  // Katie/Katherine/Kate/Kathy
  'katie': ['katie', 'katherine', 'kate', 'kathy', 'catherine'],
  'kate': ['katie', 'katherine', 'kate', 'kathy', 'catherine'],
  'katherine': ['katie', 'katherine', 'kate', 'kathy', 'catherine'],
  'kathy': ['katie', 'katherine', 'kate', 'kathy', 'catherine'],
  'catherine': ['katie', 'katherine', 'kate', 'kathy', 'catherine'],
};

/**
 * Expand a name part to include common nicknames
 */
function expandNicknames(name: string): string[] {
  const lower = name.toLowerCase();
  return NICKNAME_MAP[lower] || [name];
}

// Helper function to format names from "LAST, FIRST" to "First Last"
function formatCandidateName(name: string): string {
  if (!name) return name;

  // Check if name is in "LAST, FIRST" format
  if (name.includes(',')) {
    const [last, first] = name.split(',').map(s => s.trim());

    // Convert to title case
    const titleCase = (str: string) => {
      return str.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
    };

    return `${titleCase(first)} ${titleCase(last)}`;
  }

  // If no comma, just apply title case
  return name.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}

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

  const { data: candidateQuarterlies } = useQuarterlyData(candidateIds, [2022, 2024, 2026]);
  const { data: committeeQuarterlies } = useCommitteeQuarterlyData(committeeIds, [2022, 2024, 2026]);

  const chartData = useMemo<ChartDatum[]>(() => {
    const map = new Map<string, ChartDatum & { sortKey: string }>();

    for (const record of candidateQuarterlies) {
      if (!record.quarterLabel || !candidateIds.includes(record.candidateId)) continue;
      // Use quarterLabel + coverageEnd to ensure uniqueness for multiple filings in same quarter
      const key = `${record.quarterLabel}-${record.coverageEnd || ''}`;
      if (!map.has(key)) {
        map.set(key, {
          quarter: getDisplayLabel(record.quarterLabel),  // Clean label for tooltip
          sortKey: record.quarterLabel  // Full label for sorting
        });
      }
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
      // Use quarterLabel + coverageEnd to ensure uniqueness for multiple filings in same quarter
      const key = `${record.quarterLabel}-${record.coverageEnd || ''}`;
      if (!map.has(key)) {
        map.set(key, {
          quarter: getDisplayLabel(record.quarterLabel),  // Clean label for tooltip
          sortKey: record.quarterLabel  // Full label for sorting
        });
      }
      const datum = map.get(key)!;
      datum[record.committeeId] =
        metric === "receipts"
          ? record.receipts
          : metric === "disbursements"
          ? record.disbursements
          : record.cashEnding;
    }

    // Sort chronologically using the full label with date
    const sorted = Array.from(map.values()).sort((a, b) => sortQuarterLabels(a.sortKey, b.sortKey));

    // Trim leading empty quarters - find first quarter with any non-zero data
    const allEntityIds = [...candidateIds, ...committeeIds];
    let firstNonEmptyIndex = 0;
    for (let i = 0; i < sorted.length; i++) {
      const quarter = sorted[i];
      const hasData = allEntityIds.some((entityId) => {
        const value = quarter[entityId];
        return typeof value === "number" && value > 0;
      });
      if (hasData) {
        firstNonEmptyIndex = i;
        break;
      }
    }

    // Remove sortKey from output - only needed for sorting
    const trimmed = sorted.slice(firstNonEmptyIndex);
    return trimmed.map(({ sortKey, ...datum }) => datum);
  }, [candidateQuarterlies, committeeQuarterlies, metric, candidateIds, committeeIds]);

  const seriesConfig = useMemo<ChartSeriesConfig[]>(() => {
    return selectedEntities.map((entity, index) => ({
      key: entity.id,
      label: entity.label,
      color:
        entity.type === "committee" && entity.color
          ? entity.color // Keep predefined committee colors (DCCC, NRCC, etc.)
          : getChartColor(index), // Use palette for candidates and other entities
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
    // Require minimum 3 characters for search
    if (searchTerm.trim().length < 3) {
      setSearchResults([]);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const trimmed = searchTerm.trim();
        let data = null;
        let error = null;

        // Parse search term
        const hasSpace = trimmed.includes(' ') && !trimmed.includes(',');
        const parts = hasSpace ? trimmed.split(/\s+/) : [];

        if (parts.length >= 2) {
          // Handle 3+ words: assume last word is last name, rest is first name
          // e.g., "Ben Ray Lujan" → "Lujan, Ben Ray"
          let first: string, last: string;

          if (parts.length > 2) {
            last = parts[parts.length - 1];
            first = parts.slice(0, -1).join(' ');
            console.log(`[Committee Search] Multi-word name: "${trimmed}" → "${last}, ${first}"`);
          } else {
            [first, last] = parts;
          }

          // Expand first name to include nicknames (e.g., "Mike" → ["mike", "michael"])
          const firstNameVariations = expandNicknames(first);
          console.log(`[Committee Search] Expanded "${first}" to: [${firstNameVariations.join(', ')}]`);

          // Run 3 queries for EACH first name variation
          const allResults: any[] = [];
          const allErrors: any[] = [];

          for (const firstVariation of firstNameVariations) {
            console.log(`[Committee Search] Running 3-query fallback for: "${firstVariation}" "${last}"`);

            // Query 1: Exact conversion "Last, First"
            const result1 = await browserClient
              .from("candidates")
              .select("candidate_id, name, party")
              .ilike("name", `%${last}, ${firstVariation}%`)
              .limit(20);

            // Query 2: Prefix match - Last starts with last word, First contains first word
            const result2 = await browserClient
              .from("candidates")
              .select("candidate_id, name, party")
              .ilike("name", `${last}%`)
              .ilike("name", `%, ${firstVariation}%`)
              .limit(20);

            // Query 3: Middle name catch - Last name starts with, First name field contains the variation
            // This catches cases like "JOHNSON, JAMES MICHAEL" when searching "Mike Johnson"
            const result3 = await browserClient
              .from("candidates")
              .select("candidate_id, name, party")
              .ilike("name", `${last}%`)
              .ilike("name", `%, %${firstVariation}%`)
              .limit(20);

            allResults.push(result1, result2, result3);
            if (result1.error) allErrors.push(result1.error);
            if (result2.error) allErrors.push(result2.error);
            if (result3.error) allErrors.push(result3.error);
          }

          // Combine and deduplicate all results across all variations
          const combinedMap = new Map<string, any>();

          allResults.forEach(result => {
            if (result.data) {
              result.data.forEach((row: any) => combinedMap.set(row.candidate_id, row));
            }
          });

          data = Array.from(combinedMap.values()).slice(0, 20);
          error = allErrors.length > 0 ? allErrors[0] : null;
        } else {
          // Single word → Match at START of last name OR START of first name (after comma)
          // Also expand nicknames
          const nameVariations = expandNicknames(trimmed);
          console.log(`[Committee Search] Single word expanded: "${trimmed}" → [${nameVariations.join(', ')}]`);

          // Make two queries for EACH variation and combine results
          const allResults: any[] = [];
          const allErrors: any[] = [];

          for (const variation of nameVariations) {
            // Query 1: Match start of last name
            const result1 = await browserClient
              .from("candidates")
              .select("candidate_id, name, party")
              .ilike("name", `${variation}%`)
              .limit(20);

            // Query 2: Match start of first name (after ", ")
            const result2 = await browserClient
              .from("candidates")
              .select("candidate_id, name, party")
              .ilike("name", `%, ${variation}%`)
              .limit(20);

            allResults.push(result1, result2);
            if (result1.error) allErrors.push(result1.error);
            if (result2.error) allErrors.push(result2.error);
          }

          // Combine and deduplicate results
          const combinedMap = new Map<string, any>();

          allResults.forEach(result => {
            if (result.data) {
              result.data.forEach((row: any) => combinedMap.set(row.candidate_id, row));
            }
          });

          data = Array.from(combinedMap.values()).slice(0, 20);
          error = allErrors.length > 0 ? allErrors[0] : null;
        }

        if (error) {
          console.error('[Committee Search] Query error:', error);
          throw error;
        }

        console.log(`[Committee Search] Found ${data?.length || 0} candidates`);

        const candidateResults: EntityResult[] =
          data?.map((row) => ({
            type: "candidate" as const,
            id: row.candidate_id,
            label: formatCandidateName(row.name),
            party: row.party,
            subtitle: row.party ?? undefined,
          })) ?? [];

        const committeeMatches = QUICK_COMMITTEES.filter((entity) =>
          entity.label.toLowerCase().includes(searchTerm.toLowerCase())
        ).map((entity) => ({ ...entity, subtitle: "Committee" }));

        if (!cancelled) {
          // Combine and limit to 8 total results
          const combined = [...committeeMatches, ...candidateResults];
          setSearchResults(combined.slice(0, 8));
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
          <h2 className="text-sm font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">Metric</h2>
          <div className="flex border border-gray-300 bg-white p-1">
            {METRIC_OPTIONS.map((option) => {
              const active = metric === option.value;
              return (
                <button
                  key={option.value}
                  onClick={() => setMetric(option.value)}
                  className={`px-4 py-2 text-xs font-semibold uppercase tracking-[0.1rem] sm:tracking-[0.2rem] transition ${
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
              className="w-full border border-gray-300 bg-white px-4 py-3 text-base sm:text-sm text-gray-900 placeholder:text-gray-400 focus:border-rb-brand-navy focus:outline-none"
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
                      <span className="text-xs uppercase tracking-[0.15rem] sm:tracking-[0.25rem] text-gray-600">
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
              className="inline-flex items-center gap-2 border border-gray-300 bg-white px-3 py-2 text-xs uppercase tracking-[0.1rem] sm:tracking-[0.2rem] text-rb-brand-navy transition hover:bg-gray-100"
            >
              <span>{entity.label}</span>
              <span className="text-gray-400">×</span>
            </button>
          ))}
        </div>
      </section>

      <section className="border-2 border-rb-brand-navy bg-white">
        <div className="flex items-center justify-between border-b border-gray-200 p-6 text-sm uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
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
        <h2 className="text-sm font-semibold uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
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
                  <div className="text-xs uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
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
                <div className="mt-4 text-[10px] uppercase tracking-[0.15rem] sm:tracking-[0.3rem] text-gray-600">
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
