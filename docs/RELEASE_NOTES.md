# Release Notes

## v2.0.0 – Next.js Labs UI

- Migrated the dashboard from the legacy Vite SPA to the new Next.js Labs application (`apps/labs`).
- Introduced Supabase-backed auth flows, including Google OAuth, password resets, and watchlist management.
- Added dedicated notification settings and bulk follow tooling.
- Updated Supabase/Google OAuth redirect URLs and Vercel environment variables (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_LABS_BASE_URL`).
- Deferred the experimental Playwright/OG share routes until the post-launch cycle (removed from the production build to keep deployments stable).

## v1.0.0 – Vite UI (archived)

- Initial public release of the Campaign Reference dashboard built with Vite/React (`frontend` workspace).
- Includes original leaderboard, district view, and export tooling.

### Helpful Git Commands

Tagging the original Vite UI release and creating a long-lived branch allows easy reference later:

```bash
# Tag the last Vite commit
git tag -a v1.0.0-vite <commit-sha> -m "Vite UI 1.0.0"

# Optional: keep a legacy branch that tracks the old UI
git branch legacy/vite-ui v1.0.0-vite
```

After the Next.js work is merged, tag it as the v2.0.0 release:

```bash
git tag -a v2.0.0 <nextjs-release-sha> -m "Next.js Labs UI 2.0.0"
```

Push tags and the legacy branch to GitHub when ready:

```bash
git push origin v1.0.0-vite v2.0.0 legacy/vite-ui
```

> Replace `<commit-sha>` with the commit you want to tag (for example `de5897e00f2315cc26beb8ea625071df29fe563a` for the current `origin/main` Vite build).
