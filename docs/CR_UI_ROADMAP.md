
# Campaign Reference — UI & Visualization Roadmap
**Goal:** Deliver a screenshot‑worthy, Bloomberg‑grade visual language for Campaign Reference that Codex/Claude can implement step‑by‑step.

---

## 0) Outcomes (Definition of “Done”)
1. **Consistent Brand**: Color/typography tokens power UI and charts from one source of truth.
2. **Premium Components**: shadcn/ui + Radix primitives themed for dark financial UI.
3. **Newsroom‑quality charts**: Reusable `<CRLineChart />` & `<CRBarChart />` with disciplined grid, ticks, labels, and annotations.
4. **Partisan but muted** color scheme; neutrals for frame; emphasis on data.
5. **One-click share** *(deferred)*: static 1200×675 (2× retina) PNG export from a dedicated `/share/*` route + Open Graph generation.
6. **Accessibility & performance**: sensible motion, tabular numerals, and predictable loading.
7. **QA checklist**: every new chart or card meets screenshot standards before merge.

---

## 1) Tech Stack & Libraries
- Framework: **Next.js (App Router)** or React SPA
- Styling: **TailwindCSS**
- Components & a11y: **shadcn/ui** (built on **Radix UI**)
- Motion: **Framer Motion**
- Icons: **lucide-react**
- Charts (**Stage 1**): **Recharts** (SVG)
- Charts (**Stage 2+**): **Visx** (for precision & custom scales)
- Export: **html-to-image** (client MVP) → **Playwright/Puppeteer** (server) → **@vercel/og + satori** (for OG)
- Tables: **TanStack Table**
- State (lightweight): **Zustand**

> Why this stack: fast to ship, top‑tier a11y, newsroom‑ready exports, and strong control over visuals.

---

## 2) Installation Commands (baseline)
```bash
# Tailwind & base deps (if not present)
npm i -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# UI kit & primitives
npm i @radix-ui/react-tooltip @radix-ui/react-dialog @radix-ui/react-dropdown-menu \
      @radix-ui/react-tabs class-variance-authority clsx tailwind-merge lucide-react

# shadcn/ui CLI (optional; or clone components directly)
npx shadcn-ui@latest init

# Charts
npm i recharts
# (later) npm i @visx/visx

# Tables
npm i @tanstack/react-table

# Motion
npm i framer-motion

# Export
npm i html-to-image
# (server export later)
npm i -D playwright
# (OG images later)
npm i @vercel/og
```

---

## 3) Project Structure (proposed)
```
src/
  app/
    share/               # Static export routes (Playwright targets / @vercel/og endpoints)
  components/
    ui/                  # shadcn/ui components
    charts/
      primitives/        # axes, grid, legend, tooltip, annotations
      CRLineChart.tsx
      CRBarChart.tsx
      CRShareCard.tsx    # 1200×675 export card
    layout/
      NavBar.tsx
      Sidebar.tsx
      KPI.tsx
      DataTable.tsx
  lib/
    theme/
      tokens.ts          # colors, typography, spacing
      chartTheme.ts      # chart colors, grid, ticks, fonts
      tailwind-plugin.ts # optional helpers (tabular nums, 0.5px borders)
    format/
      number.ts          # $3.2M formatting, sig figs, short scale
      date.ts            # Q1’25 formatting
    export/
      image.ts           # html-to-image client helpers
      playwright.ts      # server PNG export util (stage 3)
      og.ts              # @vercel/og handler (stage 3)
```

---

## 4) Design Tokens (single source of truth)

### 4.1 Brand Palette (Red Bull theme as provided)
```ts
// src/lib/theme/tokens.ts
export const colors = {
  brand: {
    navy: '#121F45',     // Primary backgrounds
    blue: '#223971',     // Secondary panels
    red:  '#CC1E4A',     // Accent/CTA
    yellow: '#FFC906',   // Logo & highlights
    white: '#FFFFFF',    // Text on dark
  },

  // Financial neutrals (Bloomberg tone)
  neutral: {
    canvas: '#0E1117',   // Chart canvas (dark)
    grid:   '#2B2F36',
    axis:   '#B2B9C3',
    anno:   '#707C91',
  },

  // Partisan (muted)
  party: {
    dem:  '#5B8AEF',
    demAlt: '#3366CC',
    gop:  '#E06A6A',
    gopAlt: '#C44D4D',
    ind:  '#F4B400',
    indAlt: '#FFD666',
    base: '#7F8FA4',     // neutral/baseline
  },

  // Financial semantics
  delta: {
    up:   '#21C36F',
    down: '#E94C49',
  },
} as const;

export const typography = {
  fontFamily: {
    ui: 'Inter, Public Sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
    display: '"Libre Baskerville", Georgia, serif',
  },
  numericFeature: {
    tabular: 'tabular-nums',
  },
  sizes: {
    xs: 11, sm: 12, base: 14, md: 16, lg: 20, xl: 24, h2: 28, h1: 32,
  }
} as const;

export const spacing = { base: 4 }; // 4px grid
```

### 4.2 Tailwind Config Additions
```js
// tailwind.config.js (snippets)
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          navy:  '#121F45',
          blue:  '#223971',
          red:   '#CC1E4A',
          yellow:'#FFC906',
          white: '#FFFFFF',
        },
        neutral: {
          canvas:'#0E1117',
          grid:  '#2B2F36',
          axis:  '#B2B9C3',
          anno:  '#707C91',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Libre Baskerville"', 'Georgia', 'serif']
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
    // optional: tailwindcss-animate
  ]
};
```

---

## 5) Chart Theme & Primitives

### 5.1 Chart Theme
```ts
// src/lib/theme/chartTheme.ts
import { colors, typography } from './tokens';

export const chartTheme = {
  bg: colors.neutral.canvas,
  gridColor: colors.neutral.grid,
  axisColor: colors.neutral.axis,
  labelFont: typography.fontFamily.ui,
  labelSize: 12,
  tickStrokeWidth: 0.5,
  gridStrokeWidth: 0.5,
  linePrimaryWidth: 2,
  lineCompareWidth: 1,
  hoverGlow: 'drop-shadow(0 0 6px rgba(255,255,255,0.15))',

  series: {
    dem: colors.party.dem,
    gop: colors.party.gop,
    ind: colors.party.ind,
    neutral: colors.party.base,
  }
} as const;
```

### 5.2 Recharts Line Chart (Stage 1)
```tsx
// src/components/charts/CRLineChart.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { chartTheme as t } from '@/lib/theme/chartTheme';

type SeriesKey = 'dem' | 'gop' | 'ind';
type Datum = { quarter: string; dem: number; gop: number; ind: number };

export function CRLineChart({ data }: { data: Datum[] }) {
  return (
    <div className="w-full h-[360px] bg-neutral-canvas rounded-md border border-neutral-grid">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 16 }}>
          <CartesianGrid stroke={t.gridColor} strokeWidth={t.gridStrokeWidth} />
          <XAxis dataKey="quarter" stroke={t.axisColor} tick={{ fontSize: t.labelSize }} />
          <YAxis stroke={t.axisColor} tick={{ fontSize: t.labelSize }} tickFormatter={(n) => `$${n}M`} />
          <Tooltip
            contentStyle={{ background: '#1C1F26', border: `1px solid ${t.gridColor}`, borderRadius: 8 }}
            labelStyle={{ color: t.axisColor, fontFamily: t.labelFont }}
            itemStyle={{ color: 'white', fontFamily: t.labelFont }}
            formatter={(v: number) => [`$${v.toFixed(1)}M`, '']}
          />
          <Line type="monotone" dataKey="dem" stroke={t.series.dem} strokeWidth={t.linePrimaryWidth} dot={false} />
          <Line type="monotone" dataKey="gop" stroke={t.series.gop} strokeWidth={t.linePrimaryWidth} dot={false} />
          <Line type="monotone" dataKey="ind" stroke={t.series.ind} strokeWidth={t.linePrimaryWidth} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### 5.3 Annotations (React overlay pattern)
```tsx
// src/components/charts/primitives/Annotation.tsx
export function Annotation({ x, y, text }: { x: number; y: number; text: string }) {
  return (
    <div style={{ position: 'absolute', left: x, top: y }} className="text-[11px] text-neutral-anno">
      {text}
    </div>
  );
}
```
> Render annotations in a parent `relative` container above the SVG to keep them sharp and flexible.

---

## 6) Share Card & Image Export

### 6.1 Share Card (1200×675)
```tsx
// src/components/charts/CRShareCard.tsx
import { CRLineChart } from './CRLineChart';

export function CRShareCard({ data, title, subtitle }: any) {
  return (
    <div style={{ width: 1200, height: 675 }}
         className="bg-brand-navy text-brand-white font-sans p-12 flex flex-col justify-between">
      <div>
        <div className="font-display text-[48px] text-brand-yellow leading-tight">Campaign Reference</div>
        <div className="mt-6 text-[18px] uppercase tracking-wide text-brand-yellow/90">{title}</div>
        <div className="text-neutral-axis text-[16px]">{subtitle}</div>
      </div>
      <div className="relative">
        <CRLineChart data={data} />
        {/* Add <Annotation /> components here if needed */}
      </div>
      <div className="text-right text-neutral-axis text-[14px]">Data via campaign-reference.com • {new Date().toISOString().slice(0,10)}</div>
    </div>
  );
}
```

### 6.2 Client Export (MVP)
```ts
// src/lib/export/image.ts
import { toPng } from 'html-to-image';

export async function exportNodeToPng(node: HTMLElement, fileName = 'chart.png') {
  const dataUrl = await toPng(node, { pixelRatio: 2 }); // retina
  const link = document.createElement('a');
  link.download = fileName;
  link.href = dataUrl;
  link.click();
}
```

### 6.3 Server Export (Stage 3: Playwright)
- Add a `/share/[slug]` route that renders only the `CRShareCard` at fixed size.
- A Node script launches **Playwright** to open that route and `page.screenshot({ path, type: 'png' })`.
- Store to S3 or return the buffer for download.

### 6.4 Open Graph (Stage 3)
- Use `@vercel/og` to render the same share card; responses cached per slug.

---

## 7) Tables & KPI Cards

### 7.1 KPI Card
```tsx
// src/components/layout/KPI.tsx
export function KPI({ label, value, delta }: { label: string; value: string; delta?: number }) {
  const deltaColor = delta && delta >= 0 ? 'text-[#21C36F]' : 'text-[#E94C49]';
  const deltaSign = !delta ? '' : delta >= 0 ? '▲' : '▼';
  return (
    <div className="rounded-md border border-neutral-grid bg-brand-blue/10 p-4">
      <div className="text-neutral-axis text-sm uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-semibold text-white tabular-nums">{value}</div>
      {delta !== undefined && (
        <div className={`text-xs ${deltaColor}`}>{deltaSign} {Math.abs(delta).toFixed(1)}% QoQ</div>
      )}
    </div>
  );
}
```

### 7.2 Data Table (TanStack)
- Use sticky headers, tabular numerals, thin row separators, and hover row highlight.
- Keep zebra striping extremely subtle (alpha on `brand.blue`).

---

## 8) Motion Guidelines (Framer Motion)
- **Load:** fade in 300–400ms; translateY 8px → 0px; ease in-out.
- **Hover on bars/lines:** 5% scale bump for bars or add `filter: drop-shadow(...)` on line hover.
- **Route transitions:** crossfade charts to avoid pop-in.

---

## 9) Accessibility & Usability
- Color contrast ≥ WCAG AA.
- Keyboard support for Tabs, Dropdowns, Tooltips.
- Tooltips must not be the only way to access values (labels/summary visible).

---

## 10) Partisan Color Rules
- Dem: `#5B8AEF` (hover `#7EA6FF`)
- GOP: `#E06A6A` (hover `#FF8C8C`)
- Ind/Other: `#F4B400` (hover `#FFD666`)
- Avoid pure red/blue; keep saturation disciplined.

---

## 11) Implementation Phases (Tickets)

### Phase A — Foundations
- [ ] Add tokens.ts & chartTheme.ts; wire Tailwind colors & fonts.
- [ ] Install shadcn/ui baseline: Card, Tabs, Tooltip, Dropdown, Dialog, Table.
- [ ] Create KPI and DataTable components with tabular numerals.
- [ ] Create CRLineChart/CRBarChart using Recharts + theme.

### Phase B — Share & Export
- [ ] Build CRShareCard (1200×675); add brand header/footer.
- [ ] Add client `exportNodeToPng` (+ “Download PNG” button).
- [ ] Create `/share/[slug]` route that renders CRShareCard only.

### Phase C — Precision & Storytelling
- [ ] Add Annotation primitives & reference lines (FEC deadlines, primaries).
- [ ] Introduce small multiples for head‑to‑head comparisons.
- [ ] Add comparison mode (candidate A vs B vs race avg).

### Phase D — Server‑Grade Output
- [ ] Playwright script to screenshot `/share/[slug]` at 1× and 2×.
- [ ] Add `@vercel/og` endpoint for social share previews.
- [ ] S3 (or local) persistence + cache headers.

### Phase E — Visx Migration (optional)
- [ ] Port CRLineChart/CRBarChart to Visx for full control.
- [ ] Custom axes/ticks/annotation layer; reference band support.
- [ ] Performance profiling (React Profiler) + memoization.

---

## 12) Sample Data Contract
```ts
type Quarter = 'Q1 2025' | 'Q2 2025' | 'Q3 2025' | 'Q4 2025' | 'Q1 2026' | 'Q2 2026' | 'Q3 2026';

export type FundraisingDatum = {
  quarter: Quarter;
  dem: number; // millions
  gop: number;
  ind: number;
};
```

---

## 13) QA Checklist (pre‑merge)
- [ ] Chart readable at 50% zoom; labels never collide; ticks ≤ 6 per axis.
- [ ] Axis/labels use `Inter` 12px; numbers tabular.
- [ ] Gridlines 0.5–1px with low contrast; background #0E1117.
- [ ] Max 3 annotations; phrased like a newsroom caption.
- [ ] Export PNG renders crisp at 1200×675 and 2400×1350.
- [ ] Footer: `Data via campaign-reference.com • YYYY‑MM‑DD`.
- [ ] Keyboard & screen reader paths valid; focus rings visible.

---

## 14) Example: Q1 2025 → Q3 2026 Series
```ts
export const demoSeries = [
  { quarter: 'Q1 2025', dem: 10.8, gop: 8.2, ind: 6.8 },
  { quarter: 'Q2 2025', dem: 11.2, gop: 8.3, ind: 6.7 },
  { quarter: 'Q3 2025', dem: 13.1, gop: 9.4, ind: 6.9 },
  { quarter: 'Q4 2025', dem: 12.6, gop:11.2, ind: 7.0 },
  { quarter: 'Q1 2026', dem: 12.0, gop:13.0, ind: 7.2 },
  { quarter: 'Q2 2026', dem: 13.7, gop:16.8, ind: 7.5 },
  { quarter: 'Q3 2026', dem: 14.3, gop:20.5, ind: 8.1 },
];
```
> Values in **millions** for the demo; plug into `<CRLineChart data={demoSeries} />`.

---

## 15) Copy & Voice
- Titles: analytical and direct — *“Quarterly Fundraising — Q1 2025 to Q3 2026”*
- Dek: short, factual — *“Cumulative dollars raised by party (in millions)”*
- Annotations: reporter tone — *“GOP peak after convention”*

---

## 16) Future Enhancements
- Candidate detail pages w/ donor-source breakdowns (small multiples).
- Map view (SVG TopoJSON, not WebGL) for screenshot clarity.
- Scenario mode: projections band + uncertainty annotation.
- Theme toggle (dark newsroom vs light print layout).

---

## 17) Six-Week Build Sequence
| Week | Focus | Key Deliverables |
| ---- | ----- | ---------------- |
| 1 | Theme scaffolding | `tokens.ts` + Tailwind config, shadcn/ui init, global typography & layout primitives |
| 2 | Data surfaces | KPI card system, TanStack table with tabular numerals, navigation shell |
| 3 | Chart primitives | `CRLineChart` + `CRBarChart` against demo data, tooltip/legend polish, motion pass |
| 4 | Share-ready views | `/share/[slug]` route, `CRShareCard`, client-side `exportNodeToPng` integration |
| 5 | Storytelling extras | Annotation primitives, comparison toggles, small multiples template |
| 6 | Hardening | Playwright export harness, accessibility audit, performance profiling + memoization plan |

> Adjust cadence as needed, but keep the chart polish (Week 3) unblocked by waiting for live data by driving against the provided demo series.

---

## 18) Review & QA Cadence
- **Design desk:** Screenshot drop in Slack 2× per week (Mon/Thu) for async critique.
- **Live review:** 30 min Tuesday pairing session to walk through in-progress components.
- **Checklist enforcement:** Phase lead confirms Section 13 criteria before merging any UI PR.
- **Regression sweeps:** Use Playwright captures from Week 6 as golden snapshots for future diffing.

---

## 19) Current Status — UI Parity Pass *(Oct 31, 2025)*
- Leaderboard and By District filters now share the same 42px control system with inline metric toggles (Total Raised/Spent/Cash) instead of the dropdown.
- Party filter pills are consistent across both surfaces—active states fill with gold, inactive states stay white with navy hover.
- Subtitle pattern aligned: each view stacks `h1` + descriptive `p` before the status badges for a newsroom tone.
- Next.js and Vite implementations mirror each other, so future styling updates can ship by touching the shared patterns once.

---

**Questions saved for later**  
- Do we standardize cumulative vs per‑quarter series sitewide?  
- Do we provide a “publication mode” with enlarged labels & margins for print?

---

**Owner:** Benjamin / Campaign Reference  
**Last Updated:** (set by CI at build time)
