'use client';

import { useState, useRef } from "react";
import type { LeaderboardCandidate } from "@/hooks/useCandidateData";
import type { MetricToggles } from "@/hooks/useFilters";
import { exportToCSV } from "@/lib/export";

interface ExportButtonProps {
  data: LeaderboardCandidate[];
  metrics: MetricToggles;
  disabled?: boolean;
}

export function ExportButton({ data, metrics, disabled }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const buttonRef = useRef<HTMLDivElement>(null);

  const handleExport = (type: "csv") => {
    if (type === "csv") {
      exportToCSV(data, metrics);
    }
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={buttonRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className="rounded-lg bg-rb-red px-4 py-2 text-sm font-semibold uppercase tracking-[0.2rem] text-white transition hover:bg-opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Export
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full z-20 mt-2 min-w-[180px] rounded-lg border border-rb-border bg-white shadow-lg">
            <button
              onClick={() => handleExport("csv")}
              className="w-full px-4 py-3 text-left text-sm text-rb-black transition hover:bg-rb-row-hover"
            >
              Export as CSV
            </button>
          </div>
        </>
      )}
    </div>
  );
}
