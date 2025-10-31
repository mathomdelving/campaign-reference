'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { FollowingList } from '@/components/follow/FollowingList';

export function UserMenu() {
  const { user, signOut } = useAuth();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [showFollowingList, setShowFollowingList] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    try {
      await signOut();
      setIsOpen(false);
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  if (!user) return null;

  return (
    <>
      <div className="relative flex items-center gap-2" ref={menuRef}>
        <button
          onClick={() => setIsOpen((prev) => !prev)}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-rb-blue hover:text-white"
        >
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z"
              clipRule="evenodd"
            />
          </svg>
          <span className="hidden sm:inline">{user.email?.split('@')[0]}</span>
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute right-0 top-full z-50 mt-2 w-56 border-2 border-rb-brand-navy bg-white py-1 shadow-lg">
            <div className="border-b border-gray-200 px-4 py-2">
              <p className="text-xs text-gray-500">Signed in as</p>
              <p className="truncate text-sm font-medium text-gray-900">{user.email}</p>
            </div>

            <button
              onClick={() => {
                setShowFollowingList(true);
                setIsOpen(false);
              }}
              className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 transition hover:bg-gray-100"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
              Watch List
            </button>

            <button
              onClick={() => {
                router.push('/settings');
                setIsOpen(false);
              }}
              className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 transition hover:bg-gray-100"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
              Notification Settings
            </button>

            <button
              onClick={handleSignOut}
              className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 transition hover:bg-gray-100"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              Sign Out
            </button>
          </div>
        )}
      </div>

      {showFollowingList && (
        <FollowingList onClose={() => setShowFollowingList(false)} />
      )}
    </>
  );
}
