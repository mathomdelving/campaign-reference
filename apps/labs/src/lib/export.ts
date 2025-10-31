'use client';

import { toPng } from "html-to-image";
import type { LeaderboardCandidate } from "@/hooks/useCandidateData";
import type { MetricToggles } from "@/hooks/useFilters";

export async function exportNodeToPng(
  node: HTMLElement,
  options?: { fileName?: string; backgroundColor?: string }
) {
  const { fileName = "share-card.png", backgroundColor = "#0E1117" } =
    options ?? {};

  const dataUrl = await toPng(node, {
    pixelRatio: 2,
    cacheBust: true,
    backgroundColor,
  });

  const anchor = document.createElement("a");
  anchor.href = dataUrl;
  anchor.download = fileName;
  anchor.click();
  anchor.remove();
}

export function exportToCSV(
  data: LeaderboardCandidate[],
  metrics: MetricToggles
) {
  // Build CSV header
  const headers = [
    "Rank",
    "Candidate",
    "Candidate ID",
    "Party",
    "State",
    "District",
  ];

  if (metrics.totalRaised) headers.push("Total Raised");
  if (metrics.totalDisbursed) headers.push("Total Spent");
  if (metrics.cashOnHand) headers.push("Cash on Hand");

  // Build CSV rows
  const rows = data.map((candidate, index) => {
    const row: (string | number)[] = [
      index + 1,
      candidate.name ?? "",
      candidate.candidate_id ?? "",
      candidate.party ?? "",
      candidate.state ?? "",
      candidate.office === "H"
        ? candidate.district ?? ""
        : candidate.office === "S"
        ? "Sen"
        : "",
    ];

    if (metrics.totalRaised)
      row.push(candidate.totalReceipts ?? 0);
    if (metrics.totalDisbursed)
      row.push(candidate.totalDisbursements ?? 0);
    if (metrics.cashOnHand) row.push(candidate.cashOnHand ?? 0);

    return row;
  });

  // Convert to CSV string
  const csvContent = [
    headers.join(","),
    ...rows.map((row) =>
      row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")
    ),
  ].join("\n");

  // Download
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `campaign-finance-leaderboard-${new Date().toISOString().split("T")[0]}.csv`
  );
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
