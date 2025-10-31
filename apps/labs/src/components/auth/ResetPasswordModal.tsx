'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface ResetPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
}

export function ResetPasswordModal({
  isOpen,
  onClose,
  onSwitchToLogin,
}: ResetPasswordModalProps) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const { resetPassword } = useAuth();

  if (!isOpen) return null;

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await resetPassword(email);
      setSuccess(true);
      setEmail('');
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to send reset email.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setEmail('');
    setError('');
    setSuccess(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="w-full max-w-md bg-white p-6 shadow-xl">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Reset Password</h2>
          <button
            onClick={handleClose}
            className="text-2xl leading-none text-gray-400 transition hover:text-gray-600"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {success && (
          <div className="mb-4 rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-700">
            <p className="mb-1 font-medium">Check your email!</p>
            <p>
              We&apos;ve sent you a password reset link. Please check your inbox
              and click the link to reset your password.
            </p>
          </div>
        )}

        {error && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {!success ? (
          <>
            <p className="mb-4 text-sm text-gray-600">
              Enter your email address and we&apos;ll send you a link to reset
              your password.
            </p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="reset-email"
                  className="mb-1 block text-sm font-medium text-gray-700"
                >
                  Email
                </label>
                <input
                  id="reset-email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  className="w-full border border-gray-300 px-3 py-2 focus:border-rb-brand-navy focus:outline-none"
                  placeholder="you@example.com"
                  disabled={loading}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-rb-brand-navy px-4 py-2 font-medium text-white transition-colors hover:bg-rb-blue disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>

            <div className="mt-6 text-center text-sm text-gray-600">
              Remember your password?{' '}
              <button
                onClick={onSwitchToLogin}
                className="font-medium text-rb-brand-navy transition hover:text-rb-blue hover:underline"
              >
                Sign in
              </button>
            </div>
          </>
        ) : (
          <div className="text-center">
            <button
              onClick={handleClose}
              className="font-medium text-rb-brand-navy transition hover:text-rb-blue hover:underline"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
