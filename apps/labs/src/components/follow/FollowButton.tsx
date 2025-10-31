'use client';

import { useEffect, useState } from "react";
import type { PostgrestError } from "@supabase/supabase-js";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabaseClient";

type FollowButtonSize = "sm" | "md" | "lg";

interface FollowButtonProps {
  candidateId: string;
  candidateName: string;
  party: string | null;
  office: string | null;
  state: string | null;
  district: string | null;
  size?: FollowButtonSize;
  showLabel?: boolean;
  onFollowChange?: (candidateId: string, isFollowing: boolean) => void;
}

const SIZE_CLASSES: Record<FollowButtonSize, string> = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
};

export function FollowButton({
  candidateId,
  candidateName,
  party,
  office,
  state,
  district,
  size = "md",
  showLabel = false,
  onFollowChange,
}: FollowButtonProps) {
  const { user } = useAuth();
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);

  useEffect(() => {
    if (!user || !candidateId) {
      setIsFollowing(false);
      return;
    }

    const checkFollowStatus = async () => {
      try {
        const { data, error } = await supabase
          .from("user_candidate_follows")
          .select("id")
          .eq("user_id", user.id)
          .eq("candidate_id", candidateId)
          .maybeSingle();

        if (error && (error as PostgrestError).code !== "PGRST116") {
          throw error;
        }

        setIsFollowing(Boolean(data));
      } catch (err) {
        console.error("Error checking follow status:", err);
      }
    };

    checkFollowStatus();
  }, [user, candidateId]);

  const handleFollowToggle = async () => {
    if (!user) {
      setShowLoginPrompt(true);
      setTimeout(() => setShowLoginPrompt(false), 3000);
      return;
    }

    setLoading(true);

    try {
      if (isFollowing) {
        const { error } = await supabase
          .from("user_candidate_follows")
          .delete()
          .eq("user_id", user.id)
          .eq("candidate_id", candidateId);

        if (error) throw error;

        setIsFollowing(false);
        onFollowChange?.(candidateId, false);
      } else {
        const { count, error: countError } = await supabase
          .from("user_candidate_follows")
          .select("*", { count: "exact", head: true })
          .eq("user_id", user.id);

        if (countError) throw countError;

        if (count !== null && count >= 50) {
          alert(
            "You have reached the maximum of 50 followed candidates. Please unfollow some candidates before adding more."
          );
          setLoading(false);
          return;
        }

        const { error } = await supabase.from("user_candidate_follows").insert({
          user_id: user.id,
          candidate_id: candidateId,
          candidate_name: candidateName,
          party,
          office,
          state,
          district,
          notification_enabled: true,
        });

        if (error) throw error;

        setIsFollowing(true);
        onFollowChange?.(candidateId, true);
      }
    } catch (err) {
      console.error("Error updating follow status:", err);
      alert("Failed to update follow status. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative inline-flex items-center">
      <button
        onClick={handleFollowToggle}
        disabled={loading}
        className={`inline-flex items-center gap-1 transition-all ${
          loading ? "cursor-wait opacity-60" : "hover:scale-110"
        }`}
        title={
          !user
            ? "Sign in to follow candidates"
            : isFollowing
            ? `Stop watching ${candidateName}`
            : `Watch ${candidateName}`
        }
      >
        {isFollowing ? (
          <svg
            className={`${SIZE_CLASSES[size]} text-rb-red`}
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
          </svg>
        ) : (
          <svg
            className={`${SIZE_CLASSES[size]} text-rb-grey hover:text-rb-red`}
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
        )}
        {showLabel && (
          <span className={`text-sm font-medium ${isFollowing ? "text-rb-red" : "text-rb-grey"}`}>
            {isFollowing ? "Watching" : "Watch"}
          </span>
        )}
      </button>

      {showLoginPrompt && (
        <div className="absolute top-full left-1/2 z-50 mt-2 -translate-x-1/2 rounded bg-gray-900 px-3 py-2 text-xs text-white shadow-lg">
          Sign in to follow candidates
          <div className="absolute -top-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 bg-gray-900" />
        </div>
      )}
    </div>
  );
}
