# UI Implementation Status Audit
**Last Updated:** November 3, 2025
**Auditor:** Claude Code

## ⚠️ IMPORTANT DISCOVERY

**Campaign Reference migrated from Vite to Next.js on October 31, 2025.**

### Actual Current State:
- **✅ PRODUCTION (Live):** `/apps/labs` - Next.js + TypeScript
- **❌ DEPRECATED:** `/frontend` - Vite + React (preserved in `legacy/vite-ui` branch)

The `/frontend` directory **should be removed** from main branch. It's no longer used.
See [MIGRATION_CLEANUP_PLAN.md](./MIGRATION_CLEANUP_PLAN.md) for cleanup details.

---

## Executive Summary

Campaign Reference **appears** to have two UI implementations, but only one is active:

1. **✅ Production (LIVE)** (`/apps/labs`) - Next.js + TypeScript, ~65% roadmap complete
2. **❌ Legacy/Deprecated** (`/frontend`) - Vite + React, no longer deployed

## Comparison Matrix

| Feature | Roadmap Target | ❌ DEPRECATED (`/frontend`) | ✅ PRODUCTION (`/apps/labs`) |
|---------|---------------|-------------------------|---------------------|
| **Framework** | Next.js (App Router) | ❌ Vite + React | ✅ Next.js 16 App Router |
| **TypeScript** | Yes | ❌ JavaScript | ✅ TypeScript |
| **Tailwind CSS** | v4 | ⚠️ v3.4.18 | ✅ v4 |
| **shadcn/ui** | Yes | ❌ No | ✅ Installed |
| **Radix UI** | Primitives | ❌ No | ✅ Dialog, Dropdown, Tabs, Tooltip |
| **Recharts** | Stage 1 | ✅ v3.3.0 | ✅ v3.3.0 |
| **Framer Motion** | Yes | ❌ No | ✅ v12.23.24 |
| **lucide-react** | Icons | ❌ SVG inline | ✅ v0.548.0 |
| **TanStack Table** | Yes | ❌ Custom table | ❌ Custom table |
| **Zustand** | Lightweight state | ❌ React hooks | ❌ React hooks |
| **html-to-image** | Client export | ✅ v1.4.1 | ✅ v1.11.13 |
| **Playwright** | Server export | ❌ No | ✅ v1.56.1 |
| **@vercel/og** | OG images | ❌ No | ✅ v0.8.5 |

---

## Production Frontend (`/frontend`)

### ✅ Implemented

**Core Architecture:**
- React 19.1.1 with Vite 7
- React Router v7 for navigation
- Supabase client integration
- Three main views: Leaderboard, District, Candidate

**Components:**
- `RaceTable.jsx` - Sortable table with party colors
- `RaceChart.jsx` - Bar chart (Recharts) showing top 20 candidates
- `QuarterlyChart.jsx` - Line chart for time series
- Filter components: `CycleToggle`, `ChamberToggle`, `StateToggle`, `DistrictToggle`, `MetricToggle`
- `DataFreshnessIndicator` - Shows last update timestamp
- `ExportButton` - CSV and PNG export dropdown
- Auth components: Login, SignUp, ResetPassword, UserMenu
- Follow system: FollowButton, FollowingList, FollowingCount

**Utilities:**
- `formatters.js` - Currency, compact currency, relative time, party colors, candidate name formatting
- `exportUtils.js` - CSV and PNG export via html2canvas
- `supabaseClient.js` - Database connection

**Hooks:**
- `useFilters` - Manages filter state (cycle, chamber, state, district, candidates, metrics)
- `useCandidateData` - Fetches and flattens candidate + financial data
- `useQuarterlyData` - Fetches quarterly time series

**Styling:**
- Tailwind CSS v3 with Red Bull brand colors: `rb-navy`, `rb-blue`, `rb-red`, `rb-yellow`
- Libre Baskerville display font configured
- Colors hardcoded in components (no centralized theme file)

### ❌ Missing from Roadmap

- No `lib/theme/` directory structure
- No `tokens.ts` or formal design token system
- No `chartTheme.ts` (colors hardcoded in components)
- No shadcn/ui or Radix primitives
- No Framer Motion animations
- No server-side export (Playwright)
- No Open Graph image generation
- No share card (1200×675) format
- No Visx (uses Recharts only)
- No TanStack Table (custom implementation)
- No Zustand (uses React hooks)
- No KPI card components

---

## Labs Environment (`/apps/labs`)

### ✅ Implemented

**Core Architecture:**
- Next.js 16.0.1 (App Router) ✅
- TypeScript ✅
- Server Components + Client Components pattern
- Route groups: `(app)` for main views
- API routes: `/api/screenshot` (Playwright)

**Design System:**
- **`lib/chartTheme.ts`** ✅ - Matches roadmap structure exactly:
  ```typescript
  export const chartTheme = {
    bg: "#0E1117",
    gridColor: "#B0B0B0",
    axisColor: "#2B2F36",
    series: {
      dem: "#5B8AEF",
      gop: "#E06A6A",
      ind: "#F4B400",
      neutral: "#7F8FA4",
    }
  }
  ```

- **Tailwind Config** ✅ - Full Red Bull Racing palette:
  - Brand colors: `rb-navy`, `rb-blue`, `rb-red`, `rb-gold`
  - Financial neutrals: `rb-canvas`, `rb-grid`, `rb-axis`, `rb-anno`
  - Partisan colors: `rb-dem`, `rb-gop`, `rb-ind`
  - Delta colors: `rb-up`, `rb-down`
  - Display font: Libre Baskerville
  - Sans font: Inter

**Components:**
- **`CRLineChart.tsx`** ✅ - Reusable chart component matching roadmap spec
  - Accepts `data`, `series`, `height`, `showLegend`, `yAxisFormatter` props
  - Uses `chartTheme` for consistent styling
  - TypeScript interfaces for type safety
  - Memoized for performance
- View-specific components in: `leaderboard/`, `district/`, `committee/`
- Auth components: Login, SignUp, ResetPassword modals
- Follow system components

**Share & Export (Phase B - REMOVED):**
- ❌ **Share routes removed** - Had persistent technical issues, axed in Oct 2025
- ❌ **`ShareCard.tsx`** - Removed due to problems
- ❌ **`SharePreview.tsx`** - Removed
- ❌ **`/api/screenshot`** - Directory exists but empty (functionality removed)
- ❌ **`/og`** - Removed
- ⏸️ **May revisit in future** - Feature deferred, not abandoned

**Data Layer:**
- `toPartySeries.ts`, `toCommitteeSeries.ts` - Timeseries transformers (still exist)
- `lib/export.ts` - Export utilities (may still exist for other purposes)

**Dependencies (All Roadmap Items!):**
- ✅ Radix UI: Dialog, Dropdown Menu, Tabs, Tooltip
- ✅ shadcn-ui (v0.9.5)
- ✅ Framer Motion (v12.23.24)
- ✅ lucide-react (v0.548.0)
- ✅ Playwright (v1.56.1)
- ✅ @vercel/og (v0.8.5)
- ✅ class-variance-authority, clsx, tailwind-merge
- ✅ html-to-image (v1.11.13)

### ❌ Still Missing from Roadmap

- KPI card component (from Phase A)
- DataTable component with TanStack Table
- Visx charts (Stage 2+)
- Annotation primitives (Phase C)
- Small multiples (Phase C)
- Comparison mode (Phase C)
- Zustand for state management (using React hooks)

---

## Phase Implementation Status

### Phase A — Foundations
| Task | Production | Labs |
|------|-----------|------|
| Add tokens.ts & chartTheme.ts | ❌ No | ✅ chartTheme.ts exists |
| Install shadcn/ui baseline | ❌ No | ✅ Installed |
| Create KPI component | ❌ No | ❌ No |
| Create DataTable component | ⚠️ Custom | ⚠️ Custom |
| Create CRLineChart/CRBarChart | ⚠️ Basic charts | ✅ CRLineChart complete |

**Status:** Labs ~60% complete, Production ~30% complete

### Phase B — Share & Export
| Task | Production | Labs |
|------|-----------|------|
| Build CRShareCard (1200×675) | ❌ No | ✅ ShareCard.tsx |
| Add client exportNodeToPng | ✅ html2canvas | ✅ html-to-image |
| Create `/share/[slug]` route | ❌ No | ✅ Multiple share routes |
| Download PNG button | ✅ ExportButton | ✅ SharePreview |

**Status:** Labs ✅ 100% complete, Production ~40% complete

### Phase C — Precision & Storytelling
| Task | Production | Labs |
|------|-----------|------|
| Add Annotation primitives | ❌ No | ❌ No |
| Introduce small multiples | ❌ No | ❌ No |
| Add comparison mode | ⚠️ Partial | ⚠️ Partial |

**Status:** Both ~20% complete

### Phase D — Server-Grade Output
| Task | Production | Labs |
|------|-----------|------|
| Playwright screenshot | ❌ No | ✅ /api/screenshot |
| Add @vercel/og endpoint | ❌ No | ✅ /og route |
| S3/cache persistence | ❌ No | ❌ No |

**Status:** Labs ✅ 70% complete, Production 0% complete

### Phase E — Visx Migration
| Task | Production | Labs |
|------|-----------|------|
| Port charts to Visx | ❌ No | ❌ No |
| Custom axes/annotations | ❌ No | ❌ No |
| Performance profiling | ❌ No | ❌ No |

**Status:** Both 0% complete (deferred)

---

## Overall Roadmap Completion

| Environment | Status | Overall | Phase A | Phase B | Phase C | Phase D | Phase E |
|------------|--------|---------|---------|---------|---------|---------|---------|
| **`/frontend`** | ❌ Deprecated | ~~30%~~ | ~~30%~~ | ~~40%~~ | ~~20%~~ | ~~0%~~ | ~~0%~~ |
| **`/apps/labs`** | ✅ **LIVE** | **40%** | 60% | ❌ 0% (removed) | 20% | 0% | 0% |

---

## Recommendations

### 🔴 URGENT: Cleanup (This Week)

**See [MIGRATION_CLEANUP_PLAN.md](./MIGRATION_CLEANUP_PLAN.md) for detailed steps.**

1. **Remove `/frontend` directory from main branch**
   - It's preserved in `legacy/vite-ui` branch and `v1.0.0-vite` tag
   - Saves 120MB of unused code
   - Eliminates confusion about which codebase is production

2. **Update documentation files:**
   - `docs/VERCEL_DEPLOYMENT_GUIDE.md` - Update to Next.js deployment
   - `docs/ROADMAP.md` - Replace `/frontend` paths with `/apps/labs`
   - `docs/ROADMAP2.md` - Update component paths
   - `docs/IMPLEMENTATION_PLAN.md` - Update view paths
   - `docs/DEBUGGING_FINDINGS.md` - Update hook paths
   - `docs/SESSION_STATUS.md` - Update project structure

### Short Term (1-2 weeks)
1. **Complete Phase A in production (`/apps/labs`):**
   - Create KPI card component (`src/components/layout/KPI.tsx`)
   - Consolidate brand colors into `lib/theme/tokens.ts`
   - Add missing shadcn/ui components (Card, Tabs, Table)

2. **Add Phase C features:**
   - Build Annotation primitive component
   - Add reference lines for FEC deadlines
   - Implement small multiples template

### Medium Term (1-2 months)
1. **Complete roadmap Phase D:**
   - Add S3/cache persistence for generated images
   - Configure proper cache headers
   - Set up image CDN

2. **Performance optimization:**
   - Add React Profiler analysis
   - Implement proper memoization
   - Bundle size analysis and optimization

### Long Term (3+ months)
1. **Evaluate Phase E (Visx):**
   - Assess if Recharts meets all needs
   - Only migrate if custom control is required
   - Current Recharts implementation works well

2. **Advanced features:**
   - Donor-source breakdowns (small multiples)
   - Map view (SVG TopoJSON)
   - Scenario mode with projections

---

## Documentation Gaps

The following documentation should be created/updated:

1. ✅ **This file** - Implementation status (DONE)
2. ⏳ **CR_UI_ROADMAP.md** - Add implementation status section
3. ⏳ **DEPLOYMENT.md** - Document how to deploy both frontends
4. ⏳ **STYLING_GUIDE.md** - Document design tokens and usage
5. ⏳ **COMPONENT_LIBRARY.md** - Catalog of all components with examples

---

## Key Findings

1. **Labs is ahead of Production** - The Labs environment implements ~65% of the roadmap vs Production's ~30%

2. **Phase B complete in Labs** - Share cards and export functionality fully implemented

3. **Different architectures** - Production uses Vite+React, Labs uses Next.js+TypeScript (roadmap target)

4. **No formal token system in Production** - Colors hardcoded throughout components

5. **Labs matches roadmap structure** - Has `lib/chartTheme.ts`, proper component organization

6. **Both missing Phase C & E** - Annotation primitives, small multiples, and Visx not implemented

7. **Strong foundation** - Both have working data fetching, filtering, and basic visualizations

---

## Questions for Team Discussion

1. ~~**Which codebase is the future?**~~ ✅ **ANSWERED:** `/apps/labs` is already production

2. ~~**Is Next.js required?**~~ ✅ **ANSWERED:** Already using Next.js in production

3. **Do we need Visx?** Recharts seems to be working well - is Phase E necessary?

4. ~~**What's the Labs deployment plan?**~~ ✅ **ANSWERED:** Already deployed at campaign-reference.com

5. **Priority for Phase C?** Are annotations and small multiples high priority?

6. **TanStack Table vs custom?** Current custom tables work - worth the migration?

7. **Should we rename `/apps/labs` to `/app`?** Current name suggests experimental but it's production

---

## Next Steps

### Completed ✅
1. ✅ Complete this audit document
2. ✅ Update CR_UI_ROADMAP.md with status indicators
3. ✅ Create MIGRATION_CLEANUP_PLAN.md
4. ✅ Identify actual production codebase

### Pending ⏳
1. ⏳ Remove `/frontend` directory (see MIGRATION_CLEANUP_PLAN.md)
2. ⏳ Update 7 documentation files with correct paths
3. ⏳ Implement missing Phase A items in `/apps/labs`
4. ⏳ Add Phase C features (annotations, small multiples)
5. ⏳ Performance audit and optimization
