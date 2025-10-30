import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { supabase } from '../utils/supabaseClient';

export default function UnsubscribeView() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [status, setStatus] = useState('loading'); // loading, success, error
  const [message, setMessage] = useState('');
  const [candidateName, setCandidateName] = useState('');

  const userId = searchParams.get('user');
  const candidateId = searchParams.get('candidate');

  useEffect(() => {
    if (!userId || !candidateId) {
      setStatus('error');
      setMessage('Invalid unsubscribe link. Missing required parameters.');
      return;
    }

    handleUnsubscribe();
  }, [userId, candidateId]);

  const handleUnsubscribe = async () => {
    try {
      // First, get the candidate name
      const { data: followData, error: followError } = await supabase
        .from('user_candidate_follows')
        .select('candidate_name')
        .eq('user_id', userId)
        .eq('candidate_id', candidateId)
        .maybeSingle();

      if (followError) throw followError;

      if (!followData) {
        setStatus('error');
        setMessage('You are not following this candidate, or this link has expired.');
        return;
      }

      setCandidateName(followData.candidate_name);

      // Disable notifications for this candidate
      const { error: updateError } = await supabase
        .from('user_candidate_follows')
        .update({ notification_enabled: false })
        .eq('user_id', userId)
        .eq('candidate_id', candidateId);

      if (updateError) throw updateError;

      setStatus('success');
      setMessage(`You have been unsubscribed from notifications for ${followData.candidate_name}.`);
    } catch (error) {
      console.error('Error unsubscribing:', error);
      setStatus('error');
      setMessage('Failed to unsubscribe. Please try again or contact support.');
    }
  };

  return (
    <div className="min-h-[calc(100vh-200px)] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        {status === 'loading' && (
          <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rb-red mx-auto"></div>
            <p className="mt-4 text-gray-600">Processing your request...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8 text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
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
            <h2 className="mt-4 text-2xl font-bold font-baskerville text-gray-900">Unsubscribed</h2>
            <p className="mt-2 text-gray-600">{message}</p>

            <div className="mt-6 space-y-3">
              <p className="text-sm text-gray-500">
                You will no longer receive email notifications when <strong>{candidateName}</strong> files new reports.
              </p>
              <p className="text-sm text-gray-500">
                You are still watching this candidate and can re-enable notifications anytime in your settings.
              </p>
            </div>

            <div className="mt-8 flex flex-col gap-3">
              <button
                onClick={() => navigate('/settings')}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-rb-red hover:bg-rb-blue transition-colors"
              >
                Go to Notification Settings
              </button>
              <button
                onClick={() => navigate('/')}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
              >
                Return to Home
              </button>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8 text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
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
            <h2 className="mt-4 text-2xl font-bold font-baskerville text-gray-900">Error</h2>
            <p className="mt-2 text-gray-600">{message}</p>

            <div className="mt-8 flex flex-col gap-3">
              <button
                onClick={() => navigate('/settings')}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-rb-red hover:bg-rb-blue transition-colors"
              >
                Go to Settings
              </button>
              <button
                onClick={() => navigate('/')}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
              >
                Return to Home
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
