'use client';

import { CRLineChart, type ChartDatum, type ChartSeriesConfig } from "@/components/CRLineChart";

export interface ShareCardProps {
  title: string;
  subtitle?: string;
  asOfDate: string;
  series: ChartDatum[];
  seriesConfig?: ChartSeriesConfig[];
  metricLabel?: string;
  attribution?: string;
}

export function ShareCard({
  title,
  subtitle,
  asOfDate,
  series,
  seriesConfig,
  metricLabel = "Quarterly totals (USD)",
  attribution = "Data via campaign-reference.com",
}: ShareCardProps) {
  return (
    <div
      style={{ width: 1200, height: 675 }}
      className="flex h-[675px] w-[1200px] flex-col justify-between rounded-[28px] border border-rb-grid bg-gradient-to-br from-rb-navy via-[#0E1A3A] to-rb-canvas p-16 text-rb-white shadow-card-glow"
    >
      <header className="flex items-start justify-between gap-6">
        <div className="space-y-4">
          <p className="font-display text-4xl uppercase tracking-[0.4rem] text-rb-yellow">
            Campaign Reference
          </p>
          <h1 className="font-display text-[56px] leading-tight text-rb-white">
            {title}
          </h1>
          {subtitle ? (
            <p className="max-w-2xl text-lg text-rb-axis">{subtitle}</p>
          ) : null}
        </div>
        <div className="rounded-xl border border-rb-grid/50 bg-rb-blue/20 px-5 py-4 text-right">
          <p className="text-xs uppercase tracking-[0.3rem] text-rb-axis/70">
            As of
          </p>
          <p className="font-display text-2xl text-rb-white">{asOfDate}</p>
          <p className="text-xs tracking-wide text-rb-axis/70">{metricLabel}</p>
        </div>
      </header>

      <section className="relative flex-1 py-6">
        <CRLineChart data={series} series={seriesConfig} height={360} />
      </section>

      <footer className="flex items-end justify-between text-sm text-rb-axis/90">
        <p>{attribution}</p>
        <p className="uppercase tracking-[0.35rem] text-rb-anno">
          Labs • Share-ready export
        </p>
      </footer>
    </div>
  );
}
