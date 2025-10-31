import { ImageResponse } from "@vercel/og";
import {
  METRIC_TITLES,
  ShareNotFoundError,
  resolveSharePayload,
} from "@/app/share/shareLoader";
import { formatCompactCurrency } from "@/utils/formatters";

export const runtime = "edge";

const BACKGROUND = "#0E1117";
const PANEL = "rgba(18, 31, 69, 0.78)";
const BORDER = "#2B2F36";
const ACCENT = "#FFC906";

function buildSearchParamsRecord(searchParams: URLSearchParams) {
  const record: Record<string, string> = {};
  for (const [key, value] of searchParams.entries()) {
    if (key === "slug") continue;
    record[key] = value;
  }
  return record;
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const slug = url.searchParams.get("slug") ?? "party-receipts-2026";

  try {
    const payload = await resolveSharePayload({
      params: { slug },
      searchParams: buildSearchParamsRecord(url.searchParams),
    });

    const metricTitle = METRIC_TITLES[payload.metric];
    const latest =
      payload.series.length > 0
        ? payload.series[payload.series.length - 1]
        : { quarter: "N/A" };

    const legend =
      payload.scope === "party"
        ? [
            { key: "dem", label: "Democrats", color: "#5B8AEF" },
            { key: "gop", label: "Republicans", color: "#E06A6A" },
            { key: "ind", label: "Independents", color: "#F4B400" },
          ]
        : [
            { key: "dccc", label: "DCCC", color: "#5B8AEF" },
            { key: "dscc", label: "DSCC", color: "#3366CC" },
            { key: "nrcc", label: "NRCC", color: "#E06A6A" },
            { key: "nrsc", label: "NRSC", color: "#C44D4D" },
          ];

    return new ImageResponse(
      (
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            background: BACKGROUND,
            padding: "64px 72px",
            color: "#E7EBF6",
            fontFamily: "Inter, sans-serif",
          }}
        >
          <header style={{ display: "flex", justifyContent: "space-between" }}>
            <div style={{ maxWidth: "60%" }}>
              <p
                style={{
                  fontFamily: '"Libre Baskerville", serif',
                  letterSpacing: "14px",
                  textTransform: "uppercase",
                  color: ACCENT,
                  fontSize: "24px",
                  margin: 0,
                }}
              >
                Campaign Reference Labs
              </p>
              <h1
                style={{
                  fontFamily: '"Libre Baskerville", serif',
                  fontSize: "64px",
                  lineHeight: "1.05",
                  marginTop: "28px",
                  marginBottom: "18px",
                }}
              >
                {metricTitle} —{" "}
                {payload.scope === "party"
                  ? "Party Comparison"
                  : "National Committees"}
              </h1>
              <p
                style={{
                  fontSize: "22px",
                  color: "#B2B9C3",
                  margin: 0,
                }}
              >
                Latest quarter: {latest.quarter}
              </p>
            </div>
            <div
              style={{
                border: `1px solid ${BORDER}`,
                background: PANEL,
                padding: "20px 24px",
                borderRadius: "18px",
                textAlign: "right",
                alignSelf: "flex-start",
              }}
            >
              <p
                style={{
                  textTransform: "uppercase",
                  letterSpacing: "8px",
                  fontSize: "14px",
                  color: "#707C91",
                  marginBottom: "8px",
                }}
              >
                As of
              </p>
              <p
                style={{
                  fontFamily: '"Libre Baskerville", serif',
                  fontSize: "36px",
                  margin: 0,
                }}
              >
                {payload.asOfDate}
              </p>
              <p
                style={{
                  fontSize: "14px",
                  color: "#707C91",
                  margin: 0,
                  marginTop: "6px",
                }}
              >
                Cycle {payload.cycle}
              </p>
            </div>
          </header>

          <section
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${legend.length}, minmax(0, 1fr))`,
              gap: "24px",
              padding: "42px",
              border: `1px solid ${BORDER}`,
              background: PANEL,
              borderRadius: "24px",
            }}
          >
            {legend.map((item) => {
              const valueRaw = Number(latest[item.key as keyof typeof latest] ?? 0);
              const value = Number.isFinite(valueRaw) ? valueRaw : 0;

              return (
                <div key={item.key} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                      textTransform: "uppercase",
                      letterSpacing: "4px",
                      fontSize: "14px",
                      color: "#B2B9C3",
                    }}
                  >
                    <span
                      style={{
                        width: "12px",
                        height: "12px",
                        borderRadius: "50%",
                        background: item.color,
                      }}
                    />
                    {item.label}
                  </div>
                  <div
                    style={{
                      fontFamily: '"Libre Baskerville", serif',
                      fontSize: "42px",
                      color: "#FFFFFF",
                    }}
                  >
                    {formatCompactCurrency(value)}
                  </div>
                </div>
              );
            })}
          </section>

          <footer
            style={{
              display: "flex",
              justifyContent: "space-between",
              color: "#707C91",
              fontSize: "18px",
              textTransform: "uppercase",
              letterSpacing: "6px",
            }}
          >
            <span>Data via campaign-reference.com</span>
            <span>Campaign Reference insights for the 2026 cycle</span>
          </footer>
        </div>
      ),
      {
        width: 1200,
        height: 675,
      }
    );
  } catch (error) {
    if (error instanceof ShareNotFoundError) {
      return new ImageResponse(
        (
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: BACKGROUND,
              color: "#E7EBF6",
              fontFamily: '"Libre Baskerville", serif',
              fontSize: "48px",
              letterSpacing: "8px",
            }}
          >
            Share view unavailable
          </div>
        ),
        { width: 1200, height: 675 }
      );
    }

    console.error("/og route error", error);
    return new Response("OG generation failed", { status: 500 });
  }
}
