'use client';

import { useEffect, useMemo, useState, useRef } from "react";
import Link from "next/link";
import { createClient } from "@supabase/supabase-js";
import { CRLineChart } from "@/components/CRLineChart";
import type { ChartDatum, ChartSeriesConfig } from "@/components/CRLineChart";
import { useQuarterlyData } from "@/hooks/useQuarterlyData";
import { useCommitteeQuarterlyData } from "@/hooks/useCommitteeQuarterlyData";
import { usePersonQuarterlyData } from "@/hooks/usePersonQuarterlyData";
import { getPartyColor, formatCurrency } from "@/utils/formatters";
import { FollowButton } from "@/components/follow/FollowButton";
import { AuthButton } from "@/components/auth/AuthButton";
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

// Nickname dictionary for common political names
const NICKNAME_MAP: Record<string, string[]> = {
  'mike': ['mike', 'michael'],
  'michael': ['mike', 'michael'],
  'jim': ['jim', 'james', 'jimmy'],
  'james': ['jim', 'james', 'jimmy'],
  'jimmy': ['jim', 'james', 'jimmy'],
  'bob': ['bob', 'robert', 'bobby'],
  'robert': ['bob', 'robert', 'bobby'],
  'bobby': ['bob', 'robert', 'bobby'],
  'bill': ['bill', 'william', 'billy'],
  'william': ['bill', 'william', 'billy'],
  'billy': ['bill', 'william', 'billy'],
  'joe': ['joe', 'joseph'],
  'joseph': ['joe', 'joseph'],
  'tom': ['tom', 'thomas'],
  'thomas': ['tom', 'thomas'],
  'dick': ['dick', 'richard', 'rick', 'ricky'],
  'richard': ['dick', 'richard', 'rick', 'ricky'],
  'rick': ['dick', 'richard', 'rick', 'ricky'],
  'ricky': ['dick', 'richard', 'rick', 'ricky'],
  'jack': ['jack', 'john', 'johnny'],
  'john': ['jack', 'john', 'johnny'],
  'johnny': ['jack', 'john', 'johnny'],
  'ben': ['ben', 'benjamin'],
  'benjamin': ['ben', 'benjamin'],
  'dan': ['dan', 'daniel', 'danny'],
  'daniel': ['dan', 'daniel', 'danny'],
  'danny': ['dan', 'daniel', 'danny'],
  'chris': ['chris', 'christopher'],
  'christopher': ['chris', 'christopher'],
  'matt': ['matt', 'matthew'],
  'matthew': ['matt', 'matthew'],
  'dave': ['dave', 'david'],
  'david': ['dave', 'david'],
  'steve': ['steve', 'steven', 'stephen'],
  'steven': ['steve', 'steven', 'stephen'],
  'stephen': ['steve', 'steven', 'stephen'],
  'tony': ['tony', 'anthony'],
  'anthony': ['tony', 'anthony'],
  'chuck': ['chuck', 'charles', 'charlie'],
  'charles': ['chuck', 'charles', 'charlie'],
  'charlie': ['chuck', 'charles', 'charlie'],
  'ed': ['ed', 'edward', 'eddie'],
  'edward': ['ed', 'edward', 'eddie'],
  'eddie': ['ed', 'edward', 'eddie'],
  'pete': ['pete', 'peter'],
  'peter': ['pete', 'peter'],
  'bernie': ['bernie', 'bernard'],
  'bernard': ['bernie', 'bernard'],
  'jon': ['jon', 'john', 'jonathan'],
  'jonathan': ['jon', 'john', 'jonathan'],
};

function expandNicknames(name: string): string[] {
  const lower = name.toLowerCase();
  return NICKNAME_MAP[lower] || [name];
}

function formatCandidateName(name: string): string {
  if (!name) return name;
  if (name.includes(',')) {
    const [last, first] = name.split(',').map(s => s.trim());
    const titleCase = (str: string) => str.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
    return `${titleCase(first)} ${titleCase(last)}`;
  }
  return name.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}

function formatCurrencyLabel(value: number) {
  if (!value) return "$0";
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${Math.round(value)}`;
}

const METRIC_OPTIONS = [
  { value: "receipts", label: "Total Raised" },
  { value: "disbursements", label: "Total Spent" },
  { value: "cashEnding", label: "Cash on Hand" },
] as const;

type MetricValue = typeof METRIC_OPTIONS[number]["value"];
type EntityType = "person" | "candidate" | "committee";

type EntitySelection = {
  type: EntityType;
  id: string;
  label: string;
  party?: string | null;
  state?: string | null;
  district?: string | null;
  office?: string | null;
  candidateId?: string | null; // For persons, the linked candidate_id for following
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

export function HomePage() {
  // UI state
  const [isActive, setIsActive] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<EntityResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Chart state
  const [metric, setMetric] = useState<MetricValue>("receipts");
  const [selectedEntities, setSelectedEntities] = useState<EntitySelection[]>([]);
  const [startQuarter, setStartQuarter] = useState<string | null>(null);
  const [endQuarter, setEndQuarter] = useState<string>("present");

  // Entity IDs for data fetching
  const personIds = useMemo(
    () => selectedEntities.filter((e) => e.type === "person").map((e) => e.id),
    [selectedEntities]
  );
  const candidateIds = useMemo(
    () => selectedEntities.filter((e) => e.type === "candidate").map((e) => e.id),
    [selectedEntities]
  );
  const committeeIds = useMemo(
    () => selectedEntities.filter((e) => e.type === "committee").map((e) => e.id),
    [selectedEntities]
  );

  // Data hooks
  const { data: personQuarterlies } = usePersonQuarterlyData(personIds, [2022, 2024, 2026]);
  const { data: candidateQuarterlies } = useQuarterlyData(candidateIds, [2022, 2024, 2026]);
  const { data: committeeQuarterlies } = useCommitteeQuarterlyData(committeeIds, [2022, 2024, 2026]);

  // Handle click outside search results
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Track which person IDs we've already tried to fetch candidate info for
  const fetchedPersonIds = useRef<Set<string>>(new Set());

  // Fetch candidate info for persons missing candidateId (needed for follow functionality)
  useEffect(() => {
    const personsNeedingCandidateId = selectedEntities.filter(
      (e) => e.type === "person" && !e.candidateId && !fetchedPersonIds.current.has(e.id)
    );

    if (personsNeedingCandidateId.length === 0) return;

    // Mark these as fetched to prevent re-fetching
    personsNeedingCandidateId.forEach((p) => fetchedPersonIds.current.add(p.id));

    (async () => {
      // Look up candidates by name for persons missing candidateId
      // Names might be in different formats: "John Fetterman" vs "FETTERMAN, JOHN"
      const candidateMatches: Record<string, { candidate_id: string; office: string; state: string; district: string }> = {};

      for (const person of personsNeedingCandidateId) {
        // Extract last name for searching (handles "First Last" format)
        const nameParts = person.label.split(' ');
        const lastName = nameParts[nameParts.length - 1];

        // Search by last name only
        const { data: candidates, error } = await browserClient
          .from("candidates")
          .select("candidate_id, name, office, state, district")
          .ilike("name", `%${lastName}%`)
          .limit(10);

        if (error) {
          continue;
        }

        if (candidates && candidates.length > 0) {
          // Try to find best match - prefer same state if available
          let bestMatch = candidates[0];
          if (person.state) {
            const sameStateMatch = candidates.find(c => c.state === person.state);
            if (sameStateMatch) {
              bestMatch = sameStateMatch;
            }
          }

          candidateMatches[person.id] = {
            candidate_id: bestMatch.candidate_id,
            office: bestMatch.office,
            state: bestMatch.state,
            district: bestMatch.district,
          };
        }
      }

      if (Object.keys(candidateMatches).length === 0) return;

      // Update selectedEntities with candidateId info
      setSelectedEntities((prev) =>
        prev.map((entity) => {
          if (entity.type === "person" && !entity.candidateId && candidateMatches[entity.id]) {
            const match = candidateMatches[entity.id];
            return {
              ...entity,
              candidateId: match.candidate_id,
              office: match.office,
              state: match.state,
              district: match.district,
            };
          }
          return entity;
        })
      );
    })();
  }, [selectedEntities]);

  // Search effect
  useEffect(() => {
    if (searchTerm.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    let cancelled = false;
    setIsSearching(true);

    (async () => {
      try {
        const trimmed = searchTerm.trim();

        // Search political_persons first
        const { data: persons, error: personsError } = await browserClient
          .from("political_persons")
          .select("person_id, display_name, party, state, district, current_office")
          .ilike("display_name", `%${trimmed}%`)
          .limit(8);

        if (personsError) {
          console.error('[Home Search] Persons query error:', personsError);
        }

        // Get person IDs to fetch their candidate records
        const personIdList = persons?.map(p => p.person_id) || [];

        // Fetch candidates linked to these persons (for follow functionality)
        let candidatesByPerson: Record<string, { candidate_id: string; office: string; state: string; district: string }[]> = {};

        if (personIdList.length > 0) {
          const { data: candidateData } = await browserClient
            .from("candidates")
            .select("candidate_id, person_id, office, state, district")
            .in("person_id", personIdList);

          // Group candidates by person_id
          candidateData?.forEach((c) => {
            if (!candidatesByPerson[c.person_id]) {
              candidatesByPerson[c.person_id] = [];
            }
            candidatesByPerson[c.person_id].push(c);
          });
        }

        const personResults: EntityResult[] = persons?.map((row) => {
          // Get the first candidate_id for this person
          const candidates = candidatesByPerson[row.person_id] || [];
          const latestCandidate = candidates[0];

          return {
            type: "person" as const,
            id: row.person_id,
            label: row.display_name,
            party: row.party,
            state: latestCandidate?.state || row.state,
            district: latestCandidate?.district || row.district,
            office: latestCandidate?.office || row.current_office,
            candidateId: latestCandidate?.candidate_id || null,
            subtitle: [row.party, row.state].filter(Boolean).join(' · ') || "Person",
          };
        }) ?? [];

        // Also search candidates table directly as fallback (for candidates not linked to political_persons)
        const { data: directCandidates, error: candidatesError } = await browserClient
          .from("candidates")
          .select("candidate_id, name, party, office, state, district")
          .ilike("name", `%${trimmed}%`)
          .limit(8);

        if (candidatesError) {
          console.error('[Home Search] Candidates query error:', candidatesError);
        }

        // Create candidate results, excluding those already found via political_persons
        const personCandidateIds = new Set(personResults.map(p => p.candidateId).filter(Boolean));
        const candidateResults: EntityResult[] = (directCandidates || [])
          .filter(c => !personCandidateIds.has(c.candidate_id))
          .map((row) => ({
            type: "candidate" as const,
            id: row.candidate_id,
            label: row.name,
            party: row.party,
            state: row.state,
            district: row.district,
            office: row.office,
            candidateId: row.candidate_id,
            subtitle: [row.party, row.state, row.office === 'H' ? `District ${row.district}` : 'Senate'].filter(Boolean).join(' · '),
          }));

        // Check for committee matches
        const committeeMatches = QUICK_COMMITTEES.filter((entity) =>
          entity.label.toLowerCase().includes(searchTerm.toLowerCase())
        ).map((entity) => ({ ...entity, subtitle: "Committee" }));

        if (!cancelled) {
          // Combine: committees first, then persons with candidateIds, then direct candidates, then persons without candidateIds
          const personsWithCandidates = personResults.filter(p => p.candidateId);
          const personsWithoutCandidates = personResults.filter(p => !p.candidateId);
          const combined = [...committeeMatches, ...personsWithCandidates, ...candidateResults, ...personsWithoutCandidates];
          setSearchResults(combined.slice(0, 8));
          setShowResults(true);
        }
      } catch (err) {
        console.error('[Home Search] Error:', err);
      } finally {
        if (!cancelled) {
          setIsSearching(false);
        }
      }
    })();

    return () => { cancelled = true; };
  }, [searchTerm]);

  // Chart data processing
  const { chartDataWithKeys, chartData, quarterlyTicks } = useMemo(() => {
    const map = new Map<string, ChartDatum & { sortKey: string; quarterKey: string; timestamp: number; coverageEnd: string }>();

    // Helper to process records
    const processRecord = (record: any, entityId: string, source: 'person' | 'candidate' | 'committee') => {
      if (!record.quarterLabel) return;

      let coverageEnd = record.coverageEnd;
      if (!coverageEnd && record.quarterLabel) {
        const dateMatch = record.quarterLabel.match(/(\d{4})\.(\d{2})\.(\d{2})/);
        if (dateMatch) {
          coverageEnd = `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}`;
        } else {
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
      if (!coverageEnd) return;

      const key = `${record.quarterLabel}-${coverageEnd}`;
      if (!map.has(key)) {
        const match = record.quarterLabel.match(/Q([1-4])\s+(\d{4})/);
        const quarterKey = match ? `Q${match[1]} ${match[2]}` : record.quarterLabel;
        map.set(key, {
          quarter: getDisplayLabel(record.quarterLabel),
          sortKey: record.quarterLabel,
          quarterKey,
          timestamp: new Date(coverageEnd).getTime(),
          coverageEnd,
        });
      }

      const datum = map.get(key)!;
      datum[entityId] = metric === "receipts" ? record.receipts
        : metric === "disbursements" ? record.disbursements
        : record.cashEnding;
    };

    // Process all data
    personQuarterlies.forEach((r) => personIds.includes(r.personId) && processRecord(r, r.personId, 'person'));
    candidateQuarterlies.forEach((r) => candidateIds.includes(r.candidateId) && processRecord(r, r.candidateId, 'candidate'));
    committeeQuarterlies.forEach((r) => committeeIds.includes(r.committeeId) && processRecord(r, r.committeeId, 'committee'));

    // Sort and trim
    const sorted = Array.from(map.values()).sort((a, b) => a.timestamp - b.timestamp);
    const allEntityIds = [...personIds, ...candidateIds, ...committeeIds];

    let firstNonEmptyIndex = 0;
    for (let i = 0; i < sorted.length; i++) {
      if (allEntityIds.some((id) => {
        const val = sorted[i][id];
        return typeof val === "number" && val > 0;
      })) {
        firstNonEmptyIndex = i;
        break;
      }
    }
    const trimmed = sorted.slice(firstNonEmptyIndex);

    // Calculate ticks
    const quarterSet = new Set<string>();
    trimmed.forEach((d) => {
      const match = d.sortKey.match(/Q([1-4])\s+(\d{4})/);
      if (match) quarterSet.add(`Q${match[1]} ${match[2]}`);
    });

    const sortedQuarters = Array.from(quarterSet).sort(sortQuarterLabels);
    const quarterlyTicks = sortedQuarters.map((q) => {
      const match = q.match(/Q([1-4])\s+(\d{4})/);
      if (!match) return { label: q, timestamp: 0 };
      const quarter = parseInt(match[1]);
      const year = parseInt(match[2]);
      const month = quarter * 3 - 1;
      const lastDay = new Date(year, month + 1, 0).getDate();
      return { label: q, timestamp: new Date(year, month, lastDay).getTime() };
    });

    const displayTicks = quarterlyTicks.length > 12
      ? quarterlyTicks.filter((t) => t.label.match(/Q[13]\s+\d{4}/))
      : quarterlyTicks;

    return {
      chartDataWithKeys: trimmed,
      chartData: trimmed.map(({ sortKey, quarterKey, coverageEnd, ...d }) => d),
      quarterlyTicks: displayTicks,
    };
  }, [personQuarterlies, candidateQuarterlies, committeeQuarterlies, metric, personIds, candidateIds, committeeIds]);

  // Available quarters for date range
  const availableQuarters = useMemo(() => {
    const map = new Map<string, { sortKey: string }>();
    [...personQuarterlies, ...candidateQuarterlies, ...committeeQuarterlies].forEach((r) => {
      if (!r.quarterLabel) return;
      const match = r.quarterLabel.match(/Q([1-4])\s+(\d{4})/);
      if (match) {
        const key = `Q${match[1]} ${match[2]}`;
        if (!map.has(key)) map.set(key, { sortKey: r.quarterLabel });
      }
    });
    return Array.from(map.entries())
      .map(([k, v]) => ({ quarterKey: k, sortKey: v.sortKey }))
      .sort((a, b) => sortQuarterLabels(b.sortKey, a.sortKey))
      .map(({ quarterKey }) => {
        const match = quarterKey.match(/Q([1-4])\s+(\d{4})/);
        return match ? { value: quarterKey, label: `${match[2]} - Q${match[1]}` } : { value: quarterKey, label: quarterKey };
      });
  }, [personQuarterlies, candidateQuarterlies, committeeQuarterlies]);

  // Filter chart data by date range
  const { filteredChartData, filteredQuarterlyTicks } = useMemo(() => {
    if (!startQuarter && endQuarter === "present") {
      return { filteredChartData: chartData, filteredQuarterlyTicks: quarterlyTicks };
    }
    const filtered = chartDataWithKeys.filter((d) => {
      if (startQuarter && sortQuarterLabels(d.quarterKey, startQuarter) < 0) return false;
      if (endQuarter !== "present" && sortQuarterLabels(d.quarterKey, endQuarter) > 0) return false;
      return true;
    });
    const filteredTicks = quarterlyTicks.filter((t) => {
      if (startQuarter && sortQuarterLabels(t.label, startQuarter) < 0) return false;
      if (endQuarter !== "present" && sortQuarterLabels(t.label, endQuarter) > 0) return false;
      return true;
    });
    return {
      filteredChartData: filtered.map(({ sortKey, quarterKey, coverageEnd, ...d }) => d),
      filteredQuarterlyTicks: filteredTicks,
    };
  }, [chartDataWithKeys, chartData, quarterlyTicks, startQuarter, endQuarter]);

  // Series config for chart
  const seriesConfig = useMemo<ChartSeriesConfig[]>(() => {
    return selectedEntities.map((entity, index) => ({
      key: entity.id,
      label: entity.label,
      color: entity.type === "committee" && entity.color ? entity.color : getChartColor(index),
      strokeWidth: 2,
    }));
  }, [selectedEntities]);

  // Summary data
  type SummaryData = {
    id: string;
    label: string;
    type: EntityType;
    party?: string | null;
    value: number;
    coverage?: string | null;
    candidateId?: string | null;
    office?: string | null;
    state?: string | null;
    district?: string | null;
  };

  const summaries = useMemo(() => {
    const latestById = new Map<string, SummaryData>();

    personIds.forEach((id) => {
      const entity = selectedEntities.find((e) => e.id === id && e.type === "person");
      if (!entity) return;
      const records = personQuarterlies.filter((r) => r.personId === id);
      if (!records.length) return;
      const latest = records.reduce((a, c) => (!a.coverageEnd || (c.coverageEnd && c.coverageEnd > a.coverageEnd) ? c : a));
      latestById.set(id, {
        id,
        label: entity.label,
        type: "person",
        party: entity.party,
        value: metric === "receipts" ? latest.receipts : metric === "disbursements" ? latest.disbursements : latest.cashEnding,
        coverage: latest.coverageEnd,
        candidateId: entity.candidateId,
        office: entity.office,
        state: entity.state,
        district: entity.district,
      });
    });

    candidateIds.forEach((id) => {
      const entity = selectedEntities.find((e) => e.id === id && e.type === "candidate");
      if (!entity) return;
      const records = candidateQuarterlies.filter((r) => r.candidateId === id);
      if (!records.length) return;
      const latest = records.reduce((a, c) => (!a.coverageEnd || (c.coverageEnd && c.coverageEnd > a.coverageEnd) ? c : a));
      latestById.set(id, {
        id,
        label: entity.label,
        type: "candidate",
        party: entity.party,
        value: metric === "receipts" ? latest.receipts : metric === "disbursements" ? latest.disbursements : latest.cashEnding,
        coverage: latest.coverageEnd,
        candidateId: id, // For candidates, the id IS the candidateId
        office: entity.office,
        state: entity.state,
        district: entity.district,
      });
    });

    committeeIds.forEach((id) => {
      const entity = selectedEntities.find((e) => e.id === id && e.type === "committee");
      if (!entity) return;
      const records = committeeQuarterlies.filter((r) => r.committeeId === id);
      if (!records.length) return;
      const latest = records.reduce((a, c) => (!a.coverageEnd || (c.coverageEnd && c.coverageEnd > a.coverageEnd) ? c : a));
      latestById.set(id, {
        id,
        label: entity.label,
        type: "committee",
        value: metric === "receipts" ? latest.receipts : metric === "disbursements" ? latest.disbursements : latest.cashEnding,
        coverage: latest.coverageEnd,
      });
    });

    return Array.from(latestById.values());
  }, [selectedEntities, metric, personQuarterlies, candidateQuarterlies, committeeQuarterlies, personIds, candidateIds, committeeIds]);

  // Handlers
  const handleSelectEntity = (entity: EntitySelection) => {
    setSelectedEntities((prev) => {
      if (prev.some((e) => entityKey(e) === entityKey(entity))) return prev;
      return [...prev, entity];
    });
    setSearchTerm("");
    setSearchResults([]);
    setShowResults(false);
    setIsActive(true); // Transition to active state
  };

  const handleRemoveEntity = (entity: EntitySelection) => {
    setSelectedEntities((prev) => {
      const next = prev.filter((e) => entityKey(e) !== entityKey(entity));
      if (next.length === 0) setIsActive(false); // Return to landing if all removed
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-rb-brand-navy flex flex-col">
      {/* Header */}
      <header className="w-full z-10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 pt-4 pb-6 lg:px-8">
          <Link href="/" className="font-display text-[20px] sm:text-[26px] font-semibold uppercase leading-tight tracking-[0.2rem] sm:tracking-[0.35rem]" style={{ color: '#FFC906' }}>
            <span className="block">Campaign</span>
            <span className="block">Reference</span>
          </Link>

          <div className="flex items-center gap-4 sm:gap-6">
            <nav className="hidden md:flex items-center gap-4">
              <Link href="/" className="px-4 py-2 text-sm font-medium uppercase tracking-[0.2rem] text-rb-gold transition-colors">
                Home
              </Link>
              <Link href="/leaderboard" className="px-4 py-2 text-sm font-medium uppercase tracking-[0.2rem] text-rb-grey hover:text-white transition-colors">
                Leaderboard
              </Link>
              <Link href="/district" className="px-4 py-2 text-sm font-medium uppercase tracking-[0.2rem] text-rb-grey hover:text-white transition-colors">
                By District
              </Link>
            </nav>
            <AuthButton />
          </div>
        </div>
      </header>

      {/* Main Content - Animated Container */}
      <main className={`flex-1 flex flex-col transition-all duration-500 ease-out ${isActive ? '' : 'items-center justify-center'}`}>

        {/* Landing Hero - fades/slides up when active */}
        <div className={`text-center transition-all duration-500 ease-out ${isActive ? 'opacity-0 h-0 overflow-hidden' : 'mb-10 max-w-2xl px-4'}`}>
          <h1 className="font-display text-2xl sm:text-3xl md:text-4xl text-white mb-4">
            Track Campaign Finances
          </h1>
          <p className="text-rb-grey text-base sm:text-lg">
            Search for any federal candidate and follow their campaign finances.
            Get notified when new FEC filings are submitted.
          </p>
        </div>

        {/* Search Bar - transforms position */}
        <div
          ref={searchRef}
          className={`relative transition-all duration-500 ease-out ${
            isActive
              ? 'w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6'
              : 'w-full max-w-xl px-4'
          }`}
        >
          <div className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onFocus={() => searchResults.length > 0 && setShowResults(true)}
              placeholder={isActive ? "Add another candidate or committee..." : "Search candidates..."}
              className={`w-full text-white placeholder-rb-grey focus:outline-none focus:ring-2 focus:ring-rb-gold focus:border-transparent transition-all duration-300 ${
                isActive
                  ? 'px-4 py-3 text-base bg-white/10 border border-white/20 rounded-lg'
                  : 'px-5 py-4 text-lg bg-white/10 border border-white/20 rounded-lg'
              }`}
            />
            {isSearching && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                <svg className="animate-spin h-5 w-5 text-rb-grey" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            )}
          </div>

          {/* Search Results Dropdown */}
          {showResults && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-xl overflow-hidden z-50 mx-4 sm:mx-0">
              {searchResults.map((result) => (
                <div
                  key={`${result.type}-${result.id}`}
                  className="flex items-center justify-between w-full px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-0"
                >
                  <button
                    onClick={() => handleSelectEntity(result)}
                    className="flex items-center gap-3 flex-1 text-left"
                  >
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: result.party ? getPartyColor(result.party) : '#9ca3af' }}
                    />
                    <div>
                      <div className="text-gray-900 font-medium">{result.label}</div>
                      <div className="text-sm text-gray-500">{result.subtitle}</div>
                    </div>
                  </button>
                  {/* Show follow button for candidates and persons with linked candidates */}
                  {(result.type === 'candidate' || result.candidateId) && (
                    <FollowButton
                      candidateId={result.candidateId || result.id}
                      candidateName={result.label}
                      party={result.party ?? null}
                      office={result.office ?? null}
                      state={result.state ?? null}
                      district={result.district ?? null}
                      size="md"
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* No results message */}
          {showResults && searchTerm.length >= 2 && !isSearching && searchResults.length === 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-xl p-4 text-center text-gray-500 z-50 mx-4 sm:mx-0">
              No candidates found for "{searchTerm}"
            </div>
          )}
        </div>

        {/* Quick Links - only show in landing state */}
        <div className={`flex flex-wrap gap-3 justify-center transition-all duration-500 ${isActive ? 'opacity-0 h-0 overflow-hidden' : 'mt-8'}`}>
          <Link
            href="/leaderboard"
            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm transition-colors"
          >
            View Leaderboard
          </Link>
        </div>

        {/* Active State: Chart and Controls */}
        <div className={`w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 transition-all duration-500 ease-out ${isActive ? 'opacity-100' : 'opacity-0 h-0 overflow-hidden'}`}>

          {/* Selected Entities */}
          {selectedEntities.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {selectedEntities.map((entity) => (
                <button
                  key={entityKey(entity)}
                  onClick={() => handleRemoveEntity(entity)}
                  className="inline-flex items-center gap-2 bg-white/10 hover:bg-white/20 px-3 py-2 rounded-lg text-sm text-white transition-colors"
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: entity.type === "committee" && entity.color ? entity.color : getPartyColor(entity.party ?? null) }}
                  />
                  <span>{entity.label}</span>
                  <span className="text-rb-grey ml-1">×</span>
                </button>
              ))}
            </div>
          )}

          {/* Controls */}
          <div className="bg-white rounded-lg p-6 mb-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-600">Metric</h2>
              <div className="flex border border-gray-300 bg-white p-1 rounded">
                {METRIC_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setMetric(option.value)}
                    className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider transition rounded ${
                      metric === option.value
                        ? "bg-rb-gold text-rb-brand-navy"
                        : "text-gray-600 hover:text-rb-brand-navy"
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-600">Date Range</h2>
              <div className="flex gap-3 items-center">
                <div className="flex items-center gap-2">
                  <label className="text-xs uppercase tracking-wider text-gray-600">From:</label>
                  <select
                    value={startQuarter || ""}
                    onChange={(e) => setStartQuarter(e.target.value || null)}
                    className="border border-gray-300 bg-white px-3 py-2 text-xs uppercase tracking-wider text-gray-900 rounded focus:border-rb-brand-navy focus:outline-none"
                  >
                    <option value="">Earliest</option>
                    {availableQuarters.map((q) => (
                      <option key={q.value} value={q.value}>{q.label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-xs uppercase tracking-wider text-gray-600">To:</label>
                  <select
                    value={endQuarter}
                    onChange={(e) => setEndQuarter(e.target.value)}
                    className="border border-gray-300 bg-white px-3 py-2 text-xs uppercase tracking-wider text-gray-900 rounded focus:border-rb-brand-navy focus:outline-none"
                  >
                    <option value="present">Present</option>
                    {availableQuarters.map((q) => (
                      <option key={q.value} value={q.value}>{q.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Quick Committees */}
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gray-200">
              <span className="text-xs uppercase tracking-wider text-gray-500">Quick add:</span>
              {QUICK_COMMITTEES.map((committee) => (
                <button
                  key={committee.id}
                  onClick={() => handleSelectEntity(committee)}
                  disabled={selectedEntities.some((e) => e.id === committee.id)}
                  className={`px-3 py-1 text-xs font-medium rounded transition ${
                    selectedEntities.some((e) => e.id === committee.id)
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {committee.label}
                </button>
              ))}
            </div>
          </div>

          {/* Chart */}
          <div className="bg-white rounded-lg overflow-hidden mb-6">
            <div className="flex items-center justify-between border-b border-gray-200 p-6 text-sm uppercase tracking-widest text-gray-600">
              <span>Quarterly Trend — {METRIC_OPTIONS.find((o) => o.value === metric)?.label}</span>
              <span>{selectedEntities.length} entities</span>
            </div>
            {filteredChartData.length === 0 ? (
              <div className="p-12 text-center text-sm text-gray-600">
                {chartData.length === 0
                  ? "Select a candidate or committee to see their financial data."
                  : "No data available for the selected date range."}
              </div>
            ) : (
              <div className="p-6">
                <CRLineChart
                  data={filteredChartData}
                  series={seriesConfig}
                  height={420}
                  yAxisFormatter={formatCurrencyLabel}
                  quarterlyTicks={filteredQuarterlyTicks}
                />
              </div>
            )}
          </div>

          {/* Summaries */}
          {summaries.length > 0 && (
            <div className="mb-6">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-rb-grey mb-4">
                Latest Filing Snapshot
              </h2>
              <div className="grid gap-4 lg:grid-cols-3">
                {summaries.map((summary) => (
                  <div key={`${summary.type}-${summary.id}`} className="bg-white rounded-lg p-5">
                    <div className="flex items-start justify-between">
                      <div className="text-xs uppercase tracking-widest text-gray-600">{summary.label}</div>
                      {(summary.type === "candidate" || (summary.type === "person" && summary.candidateId)) && (
                        <FollowButton
                          candidateId={summary.candidateId || summary.id}
                          candidateName={summary.label}
                          party={summary.party ?? null}
                          office={summary.office ?? null}
                          state={summary.state ?? null}
                          district={summary.district ?? null}
                          size="sm"
                        />
                      )}
                    </div>
                    <div className="mt-3 font-display text-2xl text-rb-brand-navy">
                      {formatCurrency(summary.value)}
                    </div>
                    <div className="mt-4 text-[10px] uppercase tracking-widest text-gray-600">
                      Updated {summary.coverage?.slice(0, 10) ?? "—"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 mt-auto">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-rb-grey">
            <p>&copy; {new Date().getFullYear()} Campaign Reference</p>
            <nav className="flex gap-6">
              <Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link>
              <Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
