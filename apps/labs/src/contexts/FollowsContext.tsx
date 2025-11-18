'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabaseClient';
import type { PostgrestError } from '@supabase/supabase-js';

interface FollowsContextValue {
  followedCandidateIds: Set<string>;
  isFollowing: (candidateId: string) => boolean;
  addFollow: (candidateId: string, candidateData: FollowCandidateData) => Promise<void>;
  removeFollow: (candidateId: string) => Promise<void>;
  refreshFollows: () => Promise<void>;
  loading: boolean;
  followCount: number;
}

interface FollowCandidateData {
  candidateName: string;
  party: string | null;
  office: string | null;
  state: string | null;
  district: string | null;
}

const FollowsContext = createContext<FollowsContextValue | undefined>(undefined);

export function FollowsProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [followedCandidateIds, setFollowedCandidateIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  const fetchFollows = useCallback(async () => {
    if (!user) {
      setFollowedCandidateIds(new Set());
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('user_candidate_follows')
        .select('candidate_id')
        .eq('user_id', user.id);

      if (error && (error as PostgrestError).code !== 'PGRST116') {
        throw error;
      }

      const ids = new Set((data ?? []).map(row => row.candidate_id));
      setFollowedCandidateIds(ids);
    } catch (err) {
      console.error('[FollowsContext] Error fetching follows:', err);
      setFollowedCandidateIds(new Set());
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchFollows();
  }, [fetchFollows]);

  const isFollowing = useCallback((candidateId: string): boolean => {
    return followedCandidateIds.has(candidateId);
  }, [followedCandidateIds]);

  const addFollow = useCallback(async (
    candidateId: string,
    candidateData: FollowCandidateData
  ) => {
    if (!user) {
      throw new Error('User must be logged in to follow candidates');
    }

    // Check 50-candidate limit
    if (followedCandidateIds.size >= 50) {
      throw new Error('You have reached the maximum of 50 followed candidates. Please unfollow some candidates before adding more.');
    }

    const { error } = await supabase.from('user_candidate_follows').insert({
      user_id: user.id,
      candidate_id: candidateId,
      candidate_name: candidateData.candidateName,
      party: candidateData.party,
      office: candidateData.office,
      state: candidateData.state,
      district: candidateData.district,
      notification_enabled: true,
    });

    if (error) throw error;

    // Optimistically update local state
    setFollowedCandidateIds(prev => new Set([...prev, candidateId]));
  }, [user, followedCandidateIds]);

  const removeFollow = useCallback(async (candidateId: string) => {
    if (!user) {
      throw new Error('User must be logged in');
    }

    const { error } = await supabase
      .from('user_candidate_follows')
      .delete()
      .eq('user_id', user.id)
      .eq('candidate_id', candidateId);

    if (error) throw error;

    // Optimistically update local state
    setFollowedCandidateIds(prev => {
      const next = new Set(prev);
      next.delete(candidateId);
      return next;
    });
  }, [user]);

  const value: FollowsContextValue = {
    followedCandidateIds,
    isFollowing,
    addFollow,
    removeFollow,
    refreshFollows: fetchFollows,
    loading,
    followCount: followedCandidateIds.size,
  };

  return (
    <FollowsContext.Provider value={value}>
      {children}
    </FollowsContext.Provider>
  );
}

export function useFollows(): FollowsContextValue {
  const context = useContext(FollowsContext);
  if (!context) {
    throw new Error('useFollows must be used within a FollowsProvider');
  }
  return context;
}
