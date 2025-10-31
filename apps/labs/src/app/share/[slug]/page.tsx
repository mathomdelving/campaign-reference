import { ShareCard } from "@/components/ShareCard";
import type { ChartSeriesConfig } from "@/components/CRLineChart";
import { METRIC_TITLES, ShareNotFoundError, resolveSharePayload } from "@/app/share/shareLoader";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

interface SharePageProps {
  params: { slug: string };
  searchParams: Record<string, string | string[] | undefined>;
}

export async function generateMetadata({
  params,
  searchParams,
}: SharePageProps): Promise<Metadata> {
  try {
    const payload = await resolveSharePayload({ params, searchParams });
    const metricTitle = METRIC_TITLES[payload.metric];
    const scopeTitle =
      payload.scope === "party" ? "Party Comparison" : "National Committees";

    return {
      title: `${metricTitle} · ${scopeTitle} · Campaign Reference Labs`,
      description: `Quarterly ${metricTitle.toLowerCase()} for the ${payload.cycle} cycle.`,
    };
  } catch (error) {
    if (error instanceof ShareNotFoundError) {
      return {
        title: "Share View Not Found · Campaign Reference Labs",
      };
    }
    throw error;
  }
}

export default async function ShareSlugPage(props: SharePageProps) {
  let payload;
  try {
    payload = await resolveSharePayload(props);
  } catch (error) {
    if (error instanceof ShareNotFoundError) {
      notFound();
    }
    throw error;
  }

  const metricTitle = METRIC_TITLES[payload.metric];

  const title =
    payload.scope === "party"
      ? `${metricTitle} by Party`
      : `${metricTitle} — Party Committees`;

  const subtitle =
    payload.scope === "party"
      ? `Comparing Democrats, Republicans, and Independents across the ${payload.cycle} cycle.`
      : `DCCC, DSCC, NRCC, and NRSC performance across the ${payload.cycle} cycle.`;

  const seriesConfig: ChartSeriesConfig[] | undefined =
    payload.scope === "committee"
      ? [
          { key: "dccc", label: "DCCC", color: "#5B8AEF" },
          { key: "dscc", label: "DSCC", color: "#3366CC" },
          { key: "nrcc", label: "NRCC", color: "#E06A6A" },
          { key: "nrsc", label: "NRSC", color: "#C44D4D" },
        ]
      : undefined;

  return (
    <main className="flex min-h-screen items-center justify-center bg-rb-canvas py-16">
      <ShareCard
        title={title}
        subtitle={subtitle}
        asOfDate={payload.asOfDate}
        series={payload.series}
        seriesConfig={seriesConfig}
        metricLabel={`Quarterly ${metricTitle.toLowerCase()}`}
      />
    </main>
  );
}
