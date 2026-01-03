'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabaseClient';
import { getPartyColor } from '@/utils/formatters';

interface CandidateFollow {
  id: string;
  candidate_id: string;
  candidate_name: string;
  state: string | null;
  district: string | null;
  office: string | null;
  party: string | null;
  notification_enabled: boolean;
  ie_notification_enabled: boolean;
}

export function NotificationSettingsView() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [follows, setFollows] = useState<CandidateFollow[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  const fetchFollows = useCallback(async () => {
    if (!user) return;
    setLoading(true);
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
      alert('Unable to load notification settings right now.');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace('/leaderboard');
      return;
    }
    fetchFollows();
  }, [authLoading, user, router, fetchFollows]);

  const toggleNotification = async (
    candidateId: string,
    currentValue: boolean,
  ) => {
    if (!user) return;
    setSaving(candidateId);
    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .update({ notification_enabled: !currentValue })
        .eq('user_id', user.id)
        .eq('candidate_id', candidateId);

      if (error) throw error;
      setFollows((prev) =>
        prev.map((follow) =>
          follow.candidate_id === candidateId
            ? { ...follow, notification_enabled: !currentValue }
            : follow,
        ),
      );
    } catch (err) {
      console.error('Error toggling notification:', err);
      alert('Failed to update notification settings.');
    } finally {
      setSaving(null);
    }
  };

  const toggleIENotification = async (
    candidateId: string,
    currentValue: boolean,
  ) => {
    if (!user) return;
    setSaving(`ie-${candidateId}`);
    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .update({ ie_notification_enabled: !currentValue })
        .eq('user_id', user.id)
        .eq('candidate_id', candidateId);

      if (error) throw error;
      setFollows((prev) =>
        prev.map((follow) =>
          follow.candidate_id === candidateId
            ? { ...follow, ie_notification_enabled: !currentValue }
            : follow,
        ),
      );
    } catch (err) {
      console.error('Error toggling IE notification:', err);
      alert('Failed to update notification settings.');
    } finally {
      setSaving(null);
    }
  };

  const handleUnfollow = async (candidateId: string, candidateName: string) => {
    if (!user) return;
    if (!confirm(`Stop watching ${candidateName}?`)) return;
    try {
      const { error } = await supabase
        .from('user_candidate_follows')
        .delete()
        .eq('user_id', user.id)
        .eq('candidate_id', candidateId);

      if (error) throw error;
      setFollows((prev) =>
        prev.filter((follow) => follow.candidate_id !== candidateId),
      );
    } catch (err) {
      console.error('Error unfollowing candidate:', err);
      alert('Failed to unfollow candidate.');
    }
  };

  if (authLoading || loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <div className="text-center text-gray-500">Loading…</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-8">
        <button
          onClick={() => router.back()}
          className="mb-4 inline-flex items-center gap-1 text-sm text-gray-600 transition hover:text-gray-900"
        >
          ← Back
        </button>
        <h1 className="font-display text-3xl font-semibold text-gray-900">
          Notification Settings
        </h1>
        <p className="mt-2 text-gray-600">
          Manage email notifications for candidates you&apos;re watching.
        </p>
      </div>

      {follows.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
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
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            No candidates watched
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            Click the eye icon next to any candidate to start watching them.
          </p>
          <button
            onClick={() => router.push('/leaderboard')}
            className="mt-6 inline-flex items-center rounded-md border border-transparent bg-rb-red px-4 py-2 text-sm font-medium text-white transition hover:bg-rb-blue"
          >
            Browse Candidates
          </button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Candidate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Office
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    Campaign Filings
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    Outside Spending
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {follows.map((follow) => (
                  <tr key={follow.id} className="transition hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div
                          className="h-3 w-3 flex-shrink-0 rounded-full"
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
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                      {follow.office === 'H'
                        ? `${follow.state ?? ''}-${follow.district ?? '??'}`
                        : `${follow.state ?? ''} Senate`}
                      <div className="text-xs text-gray-500">
                        {follow.party ?? 'IND'}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-center">
                      <button
                        onClick={() =>
                          toggleNotification(
                            follow.candidate_id,
                            follow.notification_enabled,
                          )
                        }
                        disabled={saving === follow.candidate_id}
                        className={[
                          'relative inline-flex h-6 w-11 items-center rounded-full transition',
                          saving === follow.candidate_id
                            ? 'cursor-wait opacity-60'
                            : 'cursor-pointer',
                          follow.notification_enabled
                            ? 'bg-rb-red'
                            : 'bg-gray-200',
                        ].join(' ')}
                      >
                        <span
                          className={[
                            'inline-block h-4 w-4 transform rounded-full bg-white transition',
                            follow.notification_enabled
                              ? 'translate-x-6'
                              : 'translate-x-1',
                          ].join(' ')}
                        />
                      </button>
                      <div className="mt-1 text-xs text-gray-500">
                        {follow.notification_enabled ? 'On' : 'Off'}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-center">
                      <button
                        onClick={() =>
                          toggleIENotification(
                            follow.candidate_id,
                            follow.ie_notification_enabled,
                          )
                        }
                        disabled={saving === `ie-${follow.candidate_id}`}
                        className={[
                          'relative inline-flex h-6 w-11 items-center rounded-full transition',
                          saving === `ie-${follow.candidate_id}`
                            ? 'cursor-wait opacity-60'
                            : 'cursor-pointer',
                          follow.ie_notification_enabled
                            ? 'bg-rb-red'
                            : 'bg-gray-200',
                        ].join(' ')}
                      >
                        <span
                          className={[
                            'inline-block h-4 w-4 transform rounded-full bg-white transition',
                            follow.ie_notification_enabled
                              ? 'translate-x-6'
                              : 'translate-x-1',
                          ].join(' ')}
                        />
                      </button>
                      <div className="mt-1 text-xs text-gray-500">
                        {follow.ie_notification_enabled ? 'On' : 'Off'}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-center">
                      <button
                        onClick={() =>
                          handleUnfollow(
                            follow.candidate_id,
                            follow.candidate_name,
                          )
                        }
                        className="text-sm text-gray-600 transition hover:text-red-600"
                      >
                        Unfollow
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 text-sm text-gray-600">
            You&apos;re watching <strong>{follows.length}</strong> of 50
            candidates.
          </div>
        </div>
      )}
    </div>
  );
}
