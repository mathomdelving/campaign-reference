# Campaign Reference - Frontend

React + Vite frontend for the Campaign Reference FEC dashboard.

🔗 **Live Site:** [https://campaign-reference-five.vercel.app](https://campaign-reference-five.vercel.app)

---

## Tech Stack

- **React 19.1.1** - UI library
- **Vite 7.1.7** - Build tool & dev server
- **Tailwind CSS 3.4.18** - Styling
- **Recharts 3.3.0** - Data visualization
- **React Router 7.1.3** - Client-side routing
- **Supabase JS 2.76.1** - Database client
- **html2canvas 1.4.1** - Chart/table export to PNG

---

## Development

```bash
# Install dependencies
npm install

# Start dev server (localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

---

## Environment Variables

Create a `.env` file in the `frontend/` directory:

```
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_public_key
```

**Note:** The `VITE_` prefix exposes these variables to the browser. Only use the **anon (public)** key, never the service_role key.

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navigation.jsx    # Top navigation bar
│   │   │   └── Footer.jsx        # Footer with attribution
│   │   ├── toggles/
│   │   │   ├── CycleToggle.jsx   # Election cycle selector
│   │   │   ├── ChamberToggle.jsx # House/Senate/Both filter
│   │   │   ├── StateToggle.jsx   # State dropdown
│   │   │   ├── DistrictToggle.jsx# District/seat selector
│   │   │   └── MetricToggle.jsx  # Financial metrics checkboxes
│   │   ├── RaceTable.jsx         # Sortable candidate table
│   │   ├── RaceChart.jsx         # Bar chart (Leaderboard)
│   │   ├── QuarterlyChart.jsx    # Line chart (quarterly trends)
│   │   ├── DataFreshnessIndicator.jsx # "Last updated" display
│   │   └── ExportButton.jsx      # CSV/PNG export dropdown
│   ├── views/
│   │   ├── LeaderboardView.jsx   # Main rankings view
│   │   ├── DistrictView.jsx      # By-district comparison
│   │   └── CandidateView.jsx     # Candidate search & compare
│   ├── hooks/
│   │   ├── useFilters.js         # Filter state management
│   │   ├── useCandidateData.js   # Fetch candidate data
│   │   └── useQuarterlyData.js   # Fetch quarterly financials
│   ├── utils/
│   │   ├── formatters.js         # Currency & date formatting
│   │   ├── exportUtils.js        # CSV/PNG export functions
│   │   └── supabaseClient.js     # Supabase initialization
│   ├── App.jsx                   # Main app component
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Global styles
├── public/                        # Static assets
├── .env                          # Environment variables (gitignored)
├── package.json                  # Dependencies
├── vite.config.js                # Vite configuration
├── tailwind.config.js            # Tailwind configuration
└── README.md                     # This file
```

---

## Views

### 1. Leaderboard (`/leaderboard`)
- All 2026 House & Senate candidates
- Sortable by Total Raised, Total Spent, Cash on Hand
- Filters: Chamber, State, District, Party
- Toggle between table and bar chart views
- Export to CSV/PNG

### 2. By District (`/district`)
- Select state, chamber, and specific district/seat
- Compare all candidates in that race
- Party filter buttons (for primary analysis)
- Ranked list with metrics
- Quarterly trend chart

### 3. By Candidate (`/candidate`)
- Search bar with intelligent word-based matching
- Party filter buttons
- Select multiple candidates from anywhere
- Ranked list with metrics
- Quarterly trend chart

---

## Key Features

### Intelligent Search
- Word-based matching: "Mark Kelly" finds "KELLY, MARK E"
- Searches both name formats and state
- Handles partial matches

### District Validation
- Validates districts against VALID_DISTRICT_COUNTS map
- Filters out invalid/legacy districts from redistricting
- Senate classes based on candidate_id encoding

### Real-time Data
- Fetches from Supabase on filter change
- Shows "Last updated" timestamp
- Automatic refresh when data updates

### Export Functionality
- CSV export of table data
- PNG export of charts and tables using html2canvas
- Preserves formatting and styling

---

## Styling

### Red Bull Racing Theme
- Navy Blue backgrounds (`#121F45`, `#223971`)
- Red accents (`#CC1E4A`)
- Yellow highlights (`#FFC906`)
- Tailwind utility classes with custom colors

### Custom Tailwind Classes
```javascript
// tailwind.config.js
colors: {
  'rb-navy': '#121F45',
  'rb-blue': '#223971',
  'rb-red': '#CC1E4A',
  'rb-yellow': '#FFC906',
}
```

---

## Data Flow

1. **User Interaction** → Updates filters via `useFilters` hook
2. **Filter Change** → Triggers `useCandidateData` or `useQuarterlyData` hook
3. **Data Fetch** → Queries Supabase with filters
4. **State Update** → React re-renders with new data
5. **Display** → Table, chart, or list components show updated data

---

## Deployment

### Vercel (Current)
- Automatic deployments on git push to `main`
- Root Directory set to `frontend` in Vercel settings
- Environment variables configured in Vercel dashboard
- Live at: `campaign-reference-five.vercel.app`

### Build Configuration
```json
// vercel.json (in project root)
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install"
}
```

---

## Troubleshooting

### "Failed to fetch" errors
- Check that `.env` file exists with correct Supabase credentials
- Verify Supabase URL and anon key are correct
- Check browser console for CORS errors

### Blank page after build
- Run `npm run preview` to test production build locally
- Check for console errors in browser
- Verify all environment variables are set in Vercel

### Charts not rendering
- Ensure Recharts is installed: `npm install recharts`
- Check that data is properly formatted
- Verify chart component is receiving valid props

---

## Contributing

See main project README for development guidelines.

---

## License

See main project LICENSE file.
