import { useState, useEffect, useCallback } from 'react';

/**
 * Hook to load roster summary with server-computed remaining slots
 * Replaces client-side slot calculations with server data
 * 
 * @param {string} leagueId - League ID to fetch roster summary for
 * @param {string} userId - User ID (optional, defaults to current user)
 * @returns {Object} { summary, loading, error, refetch }
 */
export const useRosterSummary = (leagueId, userId = null) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRosterSummary = useCallback(async () => {
    if (!leagueId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const apiUrl = process.env.REACT_APP_BACKEND_URL || 
                    process.env.NEXT_PUBLIC_API_URL ||
                    'https://league-creator-1.preview.emergentagent.com';

      const params = userId ? `?userId=${userId}` : '';
      const response = await fetch(`${apiUrl}/api/leagues/${leagueId}/roster/summary${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch roster summary: ${response.status}`);
      }

      const data = await response.json();
      
      // Validate required fields
      if (typeof data.ownedCount !== 'number' || 
          typeof data.clubSlots !== 'number' || 
          typeof data.remaining !== 'number') {
        throw new Error('Invalid roster summary format');
      }

      setSummary(data);
    } catch (err) {
      console.error('Error fetching roster summary:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [leagueId, userId]);

  // Initial load
  useEffect(() => {
    fetchRosterSummary();
  }, [fetchRosterSummary]);

  // Subscribe to roster updates via Socket.IO (if available)
  useEffect(() => {
    if (!leagueId || typeof window === 'undefined') return;

    // Check if Socket.IO is available globally
    const socket = window.socket;
    if (!socket) return;

    const handleRosterUpdate = (updateData) => {
      // Refetch summary when roster changes
      if (updateData.leagueId === leagueId && (!userId || updateData.userId === userId)) {
        fetchRosterSummary();
      }
    };

    // Listen for roster updates
    socket.on('roster_updated', handleRosterUpdate);
    socket.on('club_purchased', handleRosterUpdate);
    socket.on('bid_won', handleRosterUpdate);

    // Cleanup
    return () => {
      socket.off('roster_updated', handleRosterUpdate);
      socket.off('club_purchased', handleRosterUpdate);
      socket.off('bid_won', handleRosterUpdate);
    };
  }, [leagueId, userId, fetchRosterSummary]);

  return {
    summary,
    loading,
    error,
    refetch: fetchRosterSummary
  };
};

export default useRosterSummary;