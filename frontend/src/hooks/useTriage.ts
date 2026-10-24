// frontend/src/hooks/useTriage.ts
import { useCallback, useState } from 'react';
import { TriageRequest, TriageResponse } from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

export function useTriage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const triage = useCallback(async (request: TriageRequest): Promise<TriageResponse> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/triage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setError(null);
    setLoading(false);
  }, []);

  return { triage, loading, error, reset };
}