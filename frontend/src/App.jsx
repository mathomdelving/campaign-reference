import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Navigation } from './components/layout/Navigation';
import LeaderboardView from './views/LeaderboardView';
import DistrictView from './views/DistrictView';
import CandidateView from './views/CandidateView';
import NotificationSettingsView from './views/NotificationSettingsView';
import UnsubscribeView from './views/UnsubscribeView';
import PrivacyPolicyView from './views/PrivacyPolicyView';
import TermsOfServiceView from './views/TermsOfServiceView';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Navigation />

        <Routes>
          <Route path="/" element={<LeaderboardView />} />
          <Route path="/leaderboard" element={<LeaderboardView />} />
          <Route path="/district" element={<DistrictView />} />
          <Route path="/candidate" element={<CandidateView />} />
          <Route path="/settings" element={<NotificationSettingsView />} />
          <Route path="/unsubscribe" element={<UnsubscribeView />} />
          <Route path="/privacy" element={<PrivacyPolicyView />} />
          <Route path="/terms" element={<TermsOfServiceView />} />
        </Routes>

        {/* Footer */}
        <footer className="mt-12 py-6 border-t border-gray-200 bg-gray-100">
          <div className="max-w-7xl mx-auto px-4">
            <div className="text-center space-y-2">
              <p className="text-sm text-gray-600">
                Data source: <a href="https://api.open.fec.gov/developers/" target="_blank" rel="noopener noreferrer" className="text-rb-red hover:text-rb-blue font-medium">FEC OpenFEC API</a>
                {' '} • {' '}
                Built with React, Tailwind CSS, and Recharts
              </p>
              <p className="text-xs text-gray-500">
                <a href="/privacy" className="text-rb-blue hover:underline">Privacy Policy</a>
                {' '} • {' '}
                <a href="/terms" className="text-rb-blue hover:underline">Terms of Service</a>
              </p>
            </div>
          </div>
        </footer>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
