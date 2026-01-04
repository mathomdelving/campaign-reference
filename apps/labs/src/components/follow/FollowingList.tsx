'use client';

import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { supabase } from '@/lib/supabaseClient';
import { getPartyColor } from '@/utils/formatters';

interface CandidateFollow {
  id: string;
  candidate_id: string;
  candidate_name: string;
  district: string | null;
  office: string | null;
  party: string | null;
  state: string | null;
  notification_enabled: boolean;
}

interface FollowingListProps {
  onClose: () => void;
}

export function FollowingList({ onClose }: FollowingListProps) {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [follows, setFollows] = useState<CandidateFollow[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchFollows = useCallback(async () => {
    if (!user) return;
    try {
      const { data, error } = await supabase
        .from('user_candidate_follows')
        .select('*')
        .eq('user_id', user.id)
        .order('followed_at', { ascending: false });

      if (error) throw error;
      setFollows((data ?? []) as CandidateFollow[]);
    } catch (err) {
      console.error('Error fetching follows:', err);
      showToast('Unable to load your watch list right now.', 'error');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchFollows();
    }
  }, [user, fetchFollows]);

  const handleUnfollow = async (candidateId: string, candidateName: string) => {
    if (!confirm(`Stop watching ${candidateName}?`)) return;
    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .delete()
        .eq('user_id', user!.id)
        .eq('candidate_id', candidateId);

      if (error) throw error;
      setFollows((prev) =>
        prev.filter((follow) => follow.candidate_id !== candidateId),
      );
    } catch (err) {
      console.error('Error unfollowing candidate:', err);
      showToast('Failed to unfollow candidate. Please try again.', 'error');
    }
  };

  const handleClearAll = async () => {
    if (follows.length === 0) return;
    if (!confirm(`Stop watching all ${follows.length} candidates?`)) return;

    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .delete()
        .eq('user_id', user!.id);

      if (error) throw error;
      setFollows([]);
    } catch (err) {
      console.error('Error clearing watch list:', err);
      showToast('Failed to clear watch list. Please try again.', 'error');
    }
  };

  const handleToggleNotifications = async (
    candidateId: string,
    currentState: boolean,
  ) => {
    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .update({ notification_enabled: !currentState })
        .eq('user_id', user!.id)
        .eq('candidate_id', candidateId);

      if (error) throw error;

      setFollows((prev) =>
        prev.map((follow) =>
          follow.candidate_id === candidateId
            ? { ...follow, notification_enabled: !currentState }
            : follow,
        ),
      );
    } catch (err) {
      console.error('Error toggling notifications:', err);
      showToast('Failed to update notification settings. Please try again.', 'error');
    }
  };

  const getLocationLabel = (follow: CandidateFollow) => {
    if (follow.office === 'S') {
      return `${follow.state ?? ''} Senate`.trim();
    }
    if (follow.district) {
      return `${follow.state ?? ''}-${follow.district}`;
    }
    return follow.state ? `${follow.state} House` : 'House';
  };

  if (!user) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="flex max-h-[80vh] w-full max-w-3xl flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900">
            Watch List ({follows.length})
          </h2>
          <button
            onClick={onClose}
            className="text-2xl leading-none text-gray-400 transition hover:text-gray-600"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="py-8 text-center text-gray-500">Loading…</div>
          ) : follows.length === 0 ? (
            <div className="py-8 text-center text-gray-600">
              <svg
                className="mx-auto mb-4 h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              <p className="mb-2">You&apos;re not watching any candidates yet.</p>
              <p className="text-sm text-gray-500">
                Click the eye icon next to a candidate to start watching them.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {follows.map((follow) => (
                <div
                  key={follow.id}
                  className="flex items-center justify-between rounded-lg bg-gray-50 p-4 transition hover:bg-gray-100"
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <div
                      className="h-3 w-3 flex-shrink-0 rounded-full"
                      style={{ backgroundColor: getPartyColor(follow.party) }}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium text-gray-900">
                        {follow.candidate_name}
                      </div>
                      <div className="text-sm text-gray-600">
                        {getLocationLabel(follow)} • {follow.party ?? 'IND'}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-shrink-0 items-center gap-2">
                    <button
                      onClick={() =>
                        handleToggleNotifications(
                          follow.candidate_id,
                          follow.notification_enabled,
                        )
                      }
                      className={`rounded p-2 transition ${
                        follow.notification_enabled
                          ? 'text-rb-blue hover:bg-blue-100'
                          : 'text-gray-400 hover:bg-gray-200'
                      }`}
                      title={
                        follow.notification_enabled
                          ? 'Notifications enabled'
                          : 'Notifications disabled'
                      }
                    >
                      <svg
                        className="h-5 w-5"
                        fill={follow.notification_enabled ? 'currentColor' : 'none'}
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        strokeWidth={follow.notification_enabled ? 0 : 2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                        />
                      </svg>
                    </button>
                    <button
                      onClick={() =>
                        handleUnfollow(follow.candidate_id, follow.candidate_name)
                      }
                      className="rounded px-3 py-1 text-sm text-red-600 transition hover:bg-red-50"
                    >
                      Unfollow
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {follows.length > 0 && (
          <div className="border-t border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <span>{follows.length} of 50 candidates maximum</span>
              <button
                onClick={handleClearAll}
                className="rounded-md px-4 py-2 font-medium text-red-600 transition hover:bg-red-50"
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
