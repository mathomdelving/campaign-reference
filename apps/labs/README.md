# Campaign Reference Labs

Campaign Reference Labs is an isolated Next.js (App Router) workspace for Red Bull Racing-inspired UI experiments, deterministic chart exports, and Open Graph previews. It consumes the existing Supabase backend in read-only mode and ships new visual treatments without touching production.

## Quickstart

```bash
npm install
npx playwright install chromium   # once, for /api/screenshot
npm run dev
```

The dev server runs at [http://localhost:3000](http://localhost:3000).

## Environment Variables

Create a `.env.local` file inside `apps/labs/`:

```env
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
# optional – overrides the origin used by /api/screenshot
NEXT_PUBLIC_LABS_BASE_URL=http://localhost:3000
```

Only the public (anon) Supabase key is required; Labs never mutates data.

## Share Routes

| Route | Description |
| --- | --- |
| `/share/party-receipts-2026` | Democrats vs. Republicans vs. Independents, quarterly fundraising |
| `/share/party-disbursements-2026` | Party spending comparison |
| `/share/party-cash-2026` | Party cash-on-hand trend |
| `/share/committee-receipts-2026` | DCCC, DSCC, NRCC, NRSC fundraising |
| `/share/committee-cash-2026` | Committee cash-on-hand |

Each share route renders a fixed 1200×675 card backed by the reusable `<ShareCard />` component and the Red Bull Racing-styled `<CRLineChart />`.

## Export Pipeline

### Client PNG (html-to-image)

1. Open the Labs landing page (`/`).
2. Use the **Download PNG** button beneath the preview card (wraps `exportNodeToPng`).

### Server PNG (Playwright)

```bash
curl "http://localhost:3000/api/screenshot?slug=party-receipts-2026" \
  --output party-receipts.png
```

The API launches Playwright with a 1200×675 viewport and returns a retina PNG. Adjust `slug`, `metric`, `cycle`, or `asOf` query params as needed.

### Open Graph Images (@vercel/og)

```bash
curl "http://localhost:3000/og?slug=committee-receipts-2026" \
  --output committee-og.png
```

The OG handler runs on the Edge runtime and returns a typographic summary card (no headless browser required).

## Core Building Blocks

- `src/components/CRLineChart.tsx` – Recharts line chart with party/committee theming.
- `src/components/ShareCard.tsx` – Fixed-size exportable card shell.
- `src/components/SharePreview.tsx` – Client wrapper that wires `html-to-image` downloads.
- `src/app/share/shareLoader.ts` – Supabase fetch + slug resolver shared by share and OG routes.
- `src/utils/toPartySeries.ts` / `toCommitteeSeries.ts` – Timeseries transformers.
- `src/lib/chartTheme.ts` – Red Bull Racing palette.
- `src/app/og/route.tsx` – Dynamic OG response using @vercel/og.
- `src/app/api/screenshot/route.ts` – Playwright-powered screenshot endpoint.

## Styling Notes

Tailwind is configured with the `rb-*` palette that mirrors the Red Bull Racing scheme (`rb-canvas`, `rb-grid`, etc.). Fonts are loaded via `next/font` (Inter for UI, Libre Baskerville for display headlines).

## Next Steps

- Add additional share renders (e.g., candidate head-to-head, small multiples).
- Layer in annotation primitives and newsroom QA checks before promoting card designs.
- Wire Labs deploys to `labs.campaign-reference.com` using Vercel previews + protected production.
