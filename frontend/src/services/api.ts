// frontend/src/services/api.ts
// Single place for all backend calls, so components don't hand-roll fetch().
import type { TriageRequest, TriageResponse, Location } from '../types/api';

const API_BASE: string = import.meta.env.VITE_API_BASE || '/api/v1';
const DEFAULT_TIMEOUT_MS = 20000;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init.headers || {}) },
      signal: controller.signal,
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        if (typeof body?.detail === 'string') detail = body.detail;
      } catch { /* non-JSON error body */ }
      throw new ApiError(res.status, detail);
    }
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(0, 'Request timed out');
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// ---- Types for endpoints that had no shared type yet ----
export interface DoctorSlot {
  doctor_id: string;
  name: string;
  language: string;
  rating: number;
  next_slot: string;
  profile_url?: string | null;
}

export interface TeleconsultResponse {
  doctors: DoctorSlot[];
  fallback_used: boolean;
  message: string;
}

export interface BookingResponse {
  booking_id: string;
  status: 'confirmed' | 'pending' | 'failed';
  message: string;
  caregiver_name: string;
  estimated_arrival?: string | null;
}

// ---- Endpoints ----
export const api = {
  triage: (body: TriageRequest) =>
    request<TriageResponse>('/triage', { method: 'POST', body: JSON.stringify(body) }),

  // TinyFish agents can be slow; the backend falls back after ~8s, so allow a bit more.
  teleconsult: (language: 'en' | 'hi' | 'hinglish', specialty?: string, preferred_time?: string) =>
    request<TeleconsultResponse>(
      '/teleconsult',
      { method: 'POST', body: JSON.stringify({ language, specialty, preferred_time }) },
      30000,
    ),

  book: (caregiver_id: string, user_location: Location, contact_phone?: string, preferred_time?: string) =>
    request<BookingResponse>('/book', {
      method: 'POST',
      body: JSON.stringify({ caregiver_id, user_location, contact_phone, preferred_time }),
    }),

};
