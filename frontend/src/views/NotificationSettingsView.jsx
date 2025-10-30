import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../utils/supabaseClient';
import { useNavigate } from 'react-router-dom';
import { getPartyColor } from '../utils/formatters';

export default function NotificationSettingsView() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [follows, setFollows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(null); // Track which candidate is being saved

  useEffect(() => {
    if (!user) {
      // Redirect to home if not logged in
      navigate('/');
      return;
    }

    fetchFollows();
  }, [user, navigate]);

  const fetchFollows = async () => {
    try {
      const { data, error } = await supabase
        .from('user_candidate_follows')
        .select('*')
        .eq('user_id', user.id)
        .order('followed_at', { ascending: false });

      if (error) throw error;

      setFollows(data || []);
    } catch (error) {
      console.error('Error fetching follows:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleNotification = async (candidateId, currentValue) => {
    setSaving(candidateId);

    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .update({ notification_enabled: !currentValue })
        .eq('user_id', user.id)
        .eq('candidate_id', candidateId);

      if (error) throw error;

      // Update local state
      setFollows(follows.map(follow =>
        follow.candidate_id === candidateId
          ? { ...follow, notification_enabled: !currentValue }
          : follow
      ));
    } catch (error) {
      console.error('Error toggling notification:', error);
      alert('Failed to update notification settings');
    } finally {
      setSaving(null);
    }
  };

  const handleUnfollow = async (candidateId, candidateName) => {
    if (!confirm(`Stop watching ${candidateName}?`)) return;

    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .delete()
        .eq('user_id', user.id)
        .eq('candidate_id', candidateId);

      if (error) throw error;

      setFollows(follows.filter(f => f.candidate_id !== candidateId));
    } catch (error) {
      console.error('Error unfollowing:', error);
      alert('Failed to unfollow candidate');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-gray-600 hover:text-gray-900 mb-4 flex items-center gap-1"
        >
          ← Back
        </button>
        <h1 className="text-3xl font-bold font-baskerville text-gray-900">Notification Settings</h1>
        <p className="mt-2 text-gray-600">
          Manage email notifications for candidates you're watching
        </p>
      </div>

      {follows.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No candidates watched</h3>
          <p className="mt-2 text-sm text-gray-500">
            Click the eye icon next to any candidate to start watching them
          </p>
          <button
            onClick={() => navigate('/')}
            className="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-rb-red hover:bg-rb-blue transition-colors"
          >
            Browse Candidates
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Candidate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Office
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email Notifications
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {follows.map((follow) => (
                  <tr key={follow.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: getPartyColor(follow.party) }}
                        />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {follow.candidate_name}
                          </div>
                          <div className="text-xs text-gray-500">
                            {follow.candidate_id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {follow.office === 'H'
                          ? `${follow.state}-${follow.district || '?'}`
                          : `${follow.state} Senate`}
                      </div>
                      <div className="text-xs text-gray-500">
                        {follow.party}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => toggleNotification(follow.candidate_id, follow.notification_enabled)}
                        disabled={saving === follow.candidate_id}
                        className={`
                          relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                          ${saving === follow.candidate_id ? 'opacity-50 cursor-wait' : 'cursor-pointer'}
                          ${follow.notification_enabled ? 'bg-rb-red' : 'bg-gray-200'}
                        `}
                      >
                        <span
                          className={`
                            inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                            ${follow.notification_enabled ? 'translate-x-6' : 'translate-x-1'}
                          `}
                        />
                      </button>
                      <div className="text-xs text-gray-500 mt-1">
                        {follow.notification_enabled ? 'Enabled' : 'Disabled'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => handleUnfollow(follow.candidate_id, follow.candidate_name)}
                        className="text-sm text-gray-600 hover:text-red-600 transition-colors"
                      >
                        Unfollow
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              You're watching <strong>{follows.length}</strong> of 50 candidates.
              {' '}
              <span className="text-gray-500">
                ({follows.filter(f => f.notification_enabled).length} with notifications enabled)
              </span>
            </p>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <svg
            className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h3 className="text-sm font-medium text-blue-900">About Email Notifications</h3>
            <p className="mt-1 text-sm text-blue-700">
              You'll receive an email when any watched candidate files a new campaign finance report with the FEC.
              The email will include their latest fundraising totals, spending, and cash on hand.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
