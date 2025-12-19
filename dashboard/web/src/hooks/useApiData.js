import { useState, useEffect, useCallback } from 'react';

// Use environment variable for API URL, fallback to localhost for development
// In Azure, set VITE_API_BASE_URL in App Service Configuration
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const POLL_INTERVAL = 5 * 60 * 1000; // 5 minutes - matches backend sync interval

export function useApiData() {
  const [data, setData] = useState({
    rewriter: null,
    adoption: null,
    feedback: null,
    status: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);

  const fetchAllData = useCallback(async () => {
    try {
      const [rewriter, adoption, feedback, status] = await Promise.all([
        fetch(`${API_BASE}/api/rewriter`).then(r => r.json()),
        fetch(`${API_BASE}/api/adoption`).then(r => r.json()),
        fetch(`${API_BASE}/api/feedback`).then(r => r.json()),
        fetch(`${API_BASE}/api/status`).then(r => r.json()),
      ]);
      
      setData({ rewriter, adoption, feedback, status });
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Trigger a manual sync on the backend (incremental by default)
  const triggerSync = useCallback(async (full = false) => {
    setIsSyncing(true);
    try {
      const response = await fetch(`${API_BASE}/api/sync?full=${full}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Sync failed');
      }
      
      // Refresh data after sync completes
      await fetchAllData();
    } catch (err) {
      console.error('Failed to trigger sync:', err);
      setError(err.message);
    } finally {
      setIsSyncing(false);
    }
  }, [fetchAllData]);

  // Initial fetch on mount
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Poll every 5 minutes for live updates (matches backend sync interval)
  useEffect(() => {
    const interval = setInterval(fetchAllData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  return { 
    data, 
    loading, 
    error, 
    lastUpdated, 
    isSyncing,
    refetch: fetchAllData,
    triggerSync, // Manual sync trigger
  };
}

// Individual hooks for pages that only need specific data
export function useRewriterData() {
  const { data, loading, error, lastUpdated, isSyncing, refetch, triggerSync } = useApiData();
  return { data: data.rewriter, loading, error, lastUpdated, isSyncing, refetch, triggerSync };
}

export function useAdoptionData() {
  const { data, loading, error, lastUpdated, isSyncing, refetch, triggerSync } = useApiData();
  return { data: data.adoption, loading, error, lastUpdated, isSyncing, refetch, triggerSync };
}

export function useFeedbackData() {
  const { data, loading, error, lastUpdated, isSyncing, refetch, triggerSync } = useApiData();
  return { data: data.feedback, loading, error, lastUpdated, isSyncing, refetch, triggerSync };
}