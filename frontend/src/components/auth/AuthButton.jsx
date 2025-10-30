import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LoginModal } from './LoginModal';
import { SignUpModal } from './SignUpModal';
import { ResetPasswordModal } from './ResetPasswordModal';
import { UserMenu } from './UserMenu';

export function AuthButton() {
  const { user, loading } = useAuth();
  const [loginOpen, setLoginOpen] = useState(false);
  const [signUpOpen, setSignUpOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <div className="animate-pulse bg-gray-300 h-8 w-16 rounded"></div>
      </div>
    );
  }

  if (user) {
    return <UserMenu />;
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setLoginOpen(true)}
          className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:bg-rb-blue hover:text-white transition-colors"
        >
          Sign In
        </button>
        <button
          onClick={() => setSignUpOpen(true)}
          className="px-3 py-2 rounded-md text-sm font-medium bg-rb-red text-white hover:bg-red-700 transition-colors"
        >
          Sign Up
        </button>
      </div>

      <LoginModal
        isOpen={loginOpen}
        onClose={() => setLoginOpen(false)}
        onSwitchToSignUp={() => {
          setLoginOpen(false);
          setSignUpOpen(true);
        }}
        onSwitchToReset={() => {
          setLoginOpen(false);
          setResetOpen(true);
        }}
      />

      <SignUpModal
        isOpen={signUpOpen}
        onClose={() => setSignUpOpen(false)}
        onSwitchToLogin={() => {
          setSignUpOpen(false);
          setLoginOpen(true);
        }}
      />

      <ResetPasswordModal
        isOpen={resetOpen}
        onClose={() => setResetOpen(false)}
        onSwitchToLogin={() => {
          setResetOpen(false);
          setLoginOpen(true);
        }}
      />
    </>
  );
}
