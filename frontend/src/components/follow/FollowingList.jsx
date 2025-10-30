import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../utils/supabaseClient';
import { getPartyColor } from '../../utils/formatters';

export function FollowingList({ onClose }) {
  const { user } = useAuth();
  const [follows, setFollows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchFollows();
    }
  }, [user]);

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

  const handleUnfollow = async (candidateId, candidateName) => {
    if (!confirm(`Stop watching ${candidateName}?`)) {
      return;
    }

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
      alert('Failed to unfollow candidate. Please try again.');
    }
  };

  const handleClearAll = async () => {
    if (!confirm(`Stop watching all ${follows.length} candidates?`)) {
      return;
    }

    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .delete()
        .eq('user_id', user.id);

      if (error) throw error;

      setFollows([]);
    } catch (error) {
      console.error('Error clearing watch list:', error);
      alert('Failed to clear watch list. Please try again.');
    }
  };

  const handleToggleNotifications = async (candidateId, currentState) => {
    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .update({ notification_enabled: !currentState })
        .eq('user_id', user.id)
        .eq('candidate_id', candidateId);

      if (error) throw error;

      setFollows(follows.map(f =>
        f.candidate_id === candidateId
          ? { ...f, notification_enabled: !currentState }
          : f
      ));
    } catch (error) {
      console.error('Error toggling notifications:', error);
      alert('Failed to update notification settings. Please try again.');
    }
  };

  const getLocationString = (follow) => {
    if (follow.office === 'S') {
      return `${follow.state} Senate`;
    } else {
      return follow.district ? `${follow.state}-${follow.district}` : `${follow.state} House`;
    }
  };

  if (!user) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">
            Watch List ({follows.length})
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : follows.length === 0 ? (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <p className="text-gray-600 mb-2">You're not watching any candidates yet.</p>
              <p className="text-sm text-gray-500">Click the eye icon next to a candidate to start watching them.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {follows.map((follow) => (
                <div
                  key={follow.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {/* Party Color Dot */}
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: getPartyColor(follow.party) }}
                    />

                    {/* Candidate Info */}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 truncate">
                        {follow.candidate_name}
                      </div>
                      <div className="text-sm text-gray-600">
                        {getLocationString(follow)} • {follow.party || 'IND'}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {/* Notification Toggle */}
                    <button
                      onClick={() => handleToggleNotifications(follow.candidate_id, follow.notification_enabled)}
                      className={`p-2 rounded transition-colors ${
                        follow.notification_enabled
                          ? 'text-rb-blue hover:bg-blue-100'
                          : 'text-gray-400 hover:bg-gray-200'
                      }`}
                      title={follow.notification_enabled ? 'Notifications enabled' : 'Notifications disabled'}
                    >
                      <svg className="h-5 w-5" fill={follow.notification_enabled ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24" strokeWidth={follow.notification_enabled ? 0 : 2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                      </svg>
                    </button>

                    {/* Unfollow Button */}
                    <button
                      onClick={() => handleUnfollow(follow.candidate_id, follow.candidate_name)}
                      className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
                    >
                      Unfollow
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {follows.length > 0 && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                {follows.length} of 50 candidates maximum
              </span>
              <button
                onClick={handleClearAll}
                className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-md transition-colors"
              >
                Clear watch list
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
