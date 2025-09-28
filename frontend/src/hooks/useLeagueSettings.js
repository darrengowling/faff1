import { useState, useEffect, useCallback } from 'react';

/**
 * Hook to load and subscribe to league settings
 * Centralizes league configuration and removes hardcoded defaults
 * 
 * @param {string} leagueId - League ID to fetch settings for
 * @returns {Object} { settings, loading, error, refetch }
 */
export const useLeagueSettings = (leagueId) => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSettings = useCallback(async () => {
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

      const response = await fetch(`${apiUrl}/api/leagues/${leagueId}/settings`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch league settings: ${response.status}`);
      }

      const data = await response.json();
      
      // Validate required fields
      if (!data.clubSlots || !data.budgetPerManager || !data.leagueSize) {
        throw new Error('Invalid league settings format');
      }

      setSettings(data);
    } catch (err) {
      console.error('Error fetching league settings:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [leagueId]);

  // Initial load
  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // Subscribe to settings updates via Socket.IO (if available)
  useEffect(() => {
    if (!leagueId || typeof window === 'undefined') return;

    // Check if Socket.IO is available globally
    const socket = window.socket;
    if (!socket) return;

    const handleSettingsUpdate = (updatedSettings) => {
      if (updatedSettings.leagueId === leagueId) {
        setSettings(updatedSettings.settings);
      }
    };

    // Listen for settings updates
    socket.on('league_settings_updated', handleSettingsUpdate);

    // Cleanup
    return () => {
      socket.off('league_settings_updated', handleSettingsUpdate);
    };
  }, [leagueId]);

  return {
    settings,
    loading,
    error,
    refetch: fetchSettings
  };
};

export default useLeagueSettings;