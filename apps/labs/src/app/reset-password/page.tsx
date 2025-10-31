'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [sessionValid, setSessionValid] = useState(false);

  const ensureSession = useCallback(async () => {
    try {
      const code = searchParams.get('code');
      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');

      if (code) {
        const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
        if (exchangeError) {
          setError(exchangeError.message);
          setInitializing(false);
          return;
        }
      } else if (accessToken && refreshToken) {
        const { error: sessionError } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        });
        if (sessionError) {
          setError(sessionError.message);
          setInitializing(false);
          return;
        }
      }

      const { data, error: sessionError } = await supabase.auth.getSession();
      if (sessionError) {
        setError(sessionError.message);
        setInitializing(false);
        return;
      }

      setSessionValid(Boolean(data.session));
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unexpected error during password recovery.';
      setError(message);
    } finally {
      setInitializing(false);
    }
  }, [searchParams]);

  useEffect(() => {
    ensureSession();
  }, [ensureSession]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    try {
      const { error: updateError } = await supabase.auth.updateUser({ password });
      if (updateError) {
        setError(updateError.message);
        return;
      }

      setSuccess(true);
      setPassword('');
      setConfirmPassword('');

      setTimeout(() => {
        router.push('/leaderboard');
      }, 2500);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to update password. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-rb-canvas px-4 py-16">
      <div className="w-full max-w-md border-2 border-rb-brand-navy bg-white p-6 shadow-xl">
        <h1 className="mb-2 font-display text-3xl font-semibold text-gray-900">
          Reset Your Password
        </h1>
        <p className="mb-6 text-sm text-gray-600">
          Enter a new password to finish resetting your Campaign Reference account.
        </p>

        {initializing ? (
          <div className="rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            Verifying your recovery link…
          </div>
        ) : !sessionValid ? (
          <div className="space-y-4">
            {error && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}
            <div className="rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
              The password reset link is invalid or has expired. Please request a new reset email
              from the sign-in screen.
            </div>
            <button
              onClick={() => router.push('/leaderboard')}
              className="w-full border border-rb-brand-navy px-4 py-2 text-sm font-semibold uppercase tracking-[0.2rem] text-rb-brand-navy transition hover:bg-rb-gold hover:text-rb-brand-navy"
            >
              Return to Sign In
            </button>
          </div>
        ) : (
          <>
            {error && (
              <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {success ? (
              <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-700">
                Password updated! Redirecting you to the app…
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label
                    htmlFor="new-password"
                    className="mb-1 block text-sm font-medium text-gray-700"
                  >
                    New password
                  </label>
                  <input
                    id="new-password"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                    minLength={6}
                    className="w-full border border-gray-300 px-3 py-2 focus:border-rb-brand-navy focus:outline-none"
                    placeholder="Choose a new password"
                    disabled={loading}
                  />
                </div>

                <div>
                  <label
                    htmlFor="confirm-password"
                    className="mb-1 block text-sm font-medium text-gray-700"
                  >
                    Confirm password
                  </label>
                  <input
                    id="confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    required
                    minLength={6}
                    className="w-full border border-gray-300 px-3 py-2 focus:border-rb-brand-navy focus:outline-none"
                    placeholder="Re-enter your password"
                    disabled={loading}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-rb-brand-navy px-4 py-2 font-medium text-white transition hover:bg-rb-blue disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading ? 'Updating…' : 'Update Password'}
                </button>
              </form>
            )}
          </>
        )}
      </div>
    </main>
  );
}
