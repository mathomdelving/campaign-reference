import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/layout/Navigation';
import LeaderboardView from './views/LeaderboardView';
import DistrictView from './views/DistrictView';
import CandidateView from './views/CandidateView';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navigation />

        <Routes>
          <Route path="/" element={<LeaderboardView />} />
          <Route path="/leaderboard" element={<LeaderboardView />} />
          <Route path="/district" element={<DistrictView />} />
          <Route path="/candidate" element={<CandidateView />} />
        </Routes>

        {/* Footer */}
        <footer className="mt-12 py-6 border-t border-gray-200 bg-gray-100">
          <div className="max-w-7xl mx-auto px-4">
            <p className="text-center text-sm text-gray-600">
              Data source: <a href="https://api.open.fec.gov/developers/" target="_blank" rel="noopener noreferrer" className="text-rb-red hover:text-rb-blue font-medium">FEC OpenFEC API</a>
              {' '} • {' '}
              Built with React, Tailwind CSS, and Recharts
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
