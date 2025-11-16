'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';

function UnsubscribeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const userId = searchParams.get('user');
  const candidateId = searchParams.get('candidate');

  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'already'>('loading');
  const [candidateName, setCandidateName] = useState<string>('');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const unsubscribe = async () => {
      if (!userId || !candidateId) {
        setStatus('error');
        setError('Invalid unsubscribe link. Missing user or candidate ID.');
        return;
      }

      try {
        // Fetch the follow record to get candidate name
        const { data: follow, error: fetchError } = await supabase
          .from('user_candidate_follows')
          .select('candidate_name, notification_enabled')
          .eq('user_id', userId)
          .eq('candidate_id', candidateId)
          .single();

        if (fetchError || !follow) {
          setStatus('error');
          setError('Could not find this notification subscription.');
          return;
        }

        setCandidateName(follow.candidate_name);

        // Check if already unsubscribed
        if (!follow.notification_enabled) {
          setStatus('already');
          return;
        }

        // Unsubscribe by disabling notifications
        const { error: updateError } = await supabase
          .from('user_candidate_follows')
          .update({ notification_enabled: false })
          .eq('user_id', userId)
          .eq('candidate_id', candidateId);

        if (updateError) {
          throw updateError;
        }

        setStatus('success');
      } catch (err) {
        console.error('Unsubscribe error:', err);
        setStatus('error');
        setError('Failed to unsubscribe. Please try again or contact support.');
      }
    };

    unsubscribe();
  }, [userId, candidateId]);

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Processing your request...</p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-lg">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <svg
              className="h-6 w-6 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-gray-900">
            Unsubscribed Successfully
          </h1>

          <p className="mb-6 text-gray-600">
            You will no longer receive email notifications about new filings from{' '}
            <strong>{candidateName}</strong>.
          </p>

          <div className="space-y-3">
            <button
              onClick={() => router.push('/settings/notifications')}
              className="w-full rounded-md bg-gray-900 px-4 py-2 text-white transition hover:bg-gray-800"
            >
              Manage All Notifications
            </button>

            <button
              onClick={() => router.push('/leaderboard')}
              className="w-full rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 transition hover:bg-gray-50"
            >
              Back to Dashboard
            </button>
          </div>

          <p className="mt-6 text-sm text-gray-500">
            You can re-enable notifications anytime from your{' '}
            <a
              href="/settings/notifications"
              className="text-blue-600 underline hover:text-blue-800"
            >
              notification settings
            </a>
            .
          </p>
        </div>
      </div>
    );
  }

  if (status === 'already') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-lg">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
            <svg
              className="h-6 w-6 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-gray-900">
            Already Unsubscribed
          </h1>

          <p className="mb-6 text-gray-600">
            You are not currently receiving email notifications from{' '}
            <strong>{candidateName}</strong>.
          </p>

          <button
            onClick={() => router.push('/settings/notifications')}
            className="w-full rounded-md bg-gray-900 px-4 py-2 text-white transition hover:bg-gray-800"
          >
            Manage Notifications
          </button>
        </div>
      </div>
    );
  }

  // Error state
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-lg">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
          <svg
            className="h-6 w-6 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </div>

        <h1 className="mb-2 text-2xl font-bold text-gray-900">
          Unsubscribe Failed
        </h1>

        <p className="mb-6 text-gray-600">{error}</p>

        <div className="space-y-3">
          <button
            onClick={() => window.location.reload()}
            className="w-full rounded-md bg-gray-900 px-4 py-2 text-white transition hover:bg-gray-800"
          >
            Try Again
          </button>

          <a
            href="mailto:support@campaign-reference.com"
            className="block w-full rounded-md border border-gray-300 bg-white px-4 py-2 text-center text-gray-700 transition hover:bg-gray-50"
          >
            Contact Support
          </a>
        </div>
      </div>
    </div>
  );
}

export default function UnsubscribePage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    }>
      <UnsubscribeContent />
    </Suspense>
  );
}
