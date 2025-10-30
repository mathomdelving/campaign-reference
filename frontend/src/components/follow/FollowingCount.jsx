import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../utils/supabaseClient';

export function FollowingCount() {
  const { user } = useAuth();
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchFollowCount();

      // Subscribe to realtime changes
      const subscription = supabase
        .channel('follow_count_changes')
        .on('postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'user_candidate_follows',
            filter: `user_id=eq.${user.id}`
          },
          () => {
            fetchFollowCount();
          }
        )
        .subscribe();

      return () => {
        subscription.unsubscribe();
      };
    } else {
      setCount(0);
      setLoading(false);
    }
  }, [user]);

  const fetchFollowCount = async () => {
    try {
      const { count: followCount, error } = await supabase
        .from('user_candidate_follows')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id);

      if (error) throw error;

      setCount(followCount || 0);
    } catch (error) {
      console.error('Error fetching follow count:', error);
      setCount(0);
    } finally {
      setLoading(false);
    }
  };

  if (!user || loading) return null;

  if (count === 0) return null;

  return (
    <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-rb-blue bg-blue-50 rounded-full">
      Following: {count}
    </span>
  );
}
