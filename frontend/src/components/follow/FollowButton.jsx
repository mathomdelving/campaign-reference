import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../utils/supabaseClient';

export function FollowButton({
  candidateId,
  candidateName,
  party,
  office,
  state,
  district,
  size = 'md',
  showLabel = false,
  onFollowChange
}) {
  const { user } = useAuth();
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);

  // Check if user is already following this candidate
  useEffect(() => {
    if (user && candidateId) {
      checkFollowStatus();
    } else {
      setIsFollowing(false);
    }
  }, [user, candidateId]);

  const checkFollowStatus = async () => {
    try {
      const { data, error } = await supabase
        .from('user_candidate_follows')
        .select('id')
        .eq('user_id', user.id)
        .eq('candidate_id', candidateId)
        .maybeSingle();

      if (error && error.code !== 'PGRST116') {
        throw error;
      }

      setIsFollowing(!!data);
    } catch (error) {
      console.error('Error checking follow status:', error);
    }
  };

  const handleFollow = async () => {
    if (!user) {
      setShowLoginPrompt(true);
      setTimeout(() => setShowLoginPrompt(false), 3000);
      return;
    }

    setLoading(true);

    try {
      if (isFollowing) {
        // Unfollow
        const { error } = await supabase
          .from('user_candidate_follows')
          .delete()
          .eq('user_id', user.id)
          .eq('candidate_id', candidateId);

        if (error) throw error;

        setIsFollowing(false);
        if (onFollowChange) onFollowChange(candidateId, false);
      } else {
        // Check if user has reached the 50-candidate limit
        const { count, error: countError } = await supabase
          .from('user_candidate_follows')
          .select('*', { count: 'exact', head: true })
          .eq('user_id', user.id);

        if (countError) throw countError;

        if (count !== null && count >= 50) {
          alert('You have reached the maximum of 50 followed candidates. Please unfollow some candidates before adding more.');
          setLoading(false);
          return;
        }

        // Follow
        const { error } = await supabase
          .from('user_candidate_follows')
          .insert({
            user_id: user.id,
            candidate_id: candidateId,
            candidate_name: candidateName,
            party: party,
            office: office,
            state: state,
            district: district,
            notification_enabled: true,
          });

        if (error) throw error;

        setIsFollowing(true);
        if (onFollowChange) onFollowChange(candidateId, true);
      }
    } catch (error) {
      console.error('Error toggling follow:', error);
      alert('Failed to update follow status. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  return (
    <div className="relative inline-block">
      <button
        onClick={handleFollow}
        disabled={loading}
        className={`
          inline-flex items-center justify-center gap-1 transition-all
          ${loading ? 'opacity-50 cursor-wait' : 'hover:scale-110'}
          ${!user ? 'cursor-pointer' : ''}
        `}
        style={{ verticalAlign: 'middle' }}
        title={!user ? 'Sign in to follow candidates' : isFollowing ? `Stop watching ${candidateName}` : `Watch ${candidateName}`}
      >
        {isFollowing ? (
          <svg
            className={`${sizeClasses[size]} text-rb-red`}
            fill="currentColor"
            viewBox="0 0 24 24"
            style={{ transform: 'translateY(-1px)' }}
          >
            <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
          </svg>
        ) : (
          <svg
            className={`${sizeClasses[size]} text-gray-400 hover:text-rb-red`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={2}
            style={{ transform: 'translateY(-1px)' }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        )}
        {showLabel && (
          <span className={`text-sm font-medium ${isFollowing ? 'text-rb-red' : 'text-gray-600'}`}>
            {isFollowing ? 'Watching' : 'Watch'}
          </span>
        )}
      </button>

      {showLoginPrompt && (
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 bg-gray-900 text-white text-xs px-3 py-2 rounded shadow-lg whitespace-nowrap z-50">
          Sign in to follow candidates
          <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45"></div>
        </div>
      )}
    </div>
  );
}
