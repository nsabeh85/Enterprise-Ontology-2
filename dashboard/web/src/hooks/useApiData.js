import { useState, useEffect, useCallback } from 'react';

// Use environment variable for API URL, fallback to localhost for development
// In Azure, set VITE_API_BASE_URL in App Service Configuration
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const POLL_INTERVAL = 30000; // 30 seconds - auto refresh

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

  // Initial fetch on mount
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Poll every 30 seconds for live updates
  useEffect(() => {
    const interval = setInterval(fetchAllData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  return { 
    data, 
    loading, 
    error, 
    lastUpdated, 
    refetch: fetchAllData 
  };
}

// Individual hooks for pages that only need specific data
export function useRewriterData() {
  const { data, loading, error, lastUpdated, refetch } = useApiData();
  return { data: data.rewriter, loading, error, lastUpdated, refetch };
}

export function useAdoptionData() {
  const { data, loading, error, lastUpdated, refetch } = useApiData();
  return { data: data.adoption, loading, error, lastUpdated, refetch };
}

export function useFeedbackData() {
  const { data, loading, error, lastUpdated, refetch } = useApiData();
  return { data: data.feedback, loading, error, lastUpdated, refetch };
}