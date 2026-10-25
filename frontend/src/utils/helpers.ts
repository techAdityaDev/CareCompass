// frontend/src/utils/helpers.ts
import type { ConversationMessage, Location } from '../types/api';

export const DEFAULT_LOCATION: Location = { lat: 28.6139, lng: 77.209 }; // Delhi NCR centre

/** Ask the browser for the user's location; fall back to Delhi NCR after 5s or on denial. */
export function getUserLocation(timeoutMs = 5000): Promise<Location> {
  return new Promise((resolve) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      resolve(DEFAULT_LOCATION);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(DEFAULT_LOCATION),
      { timeout: timeoutMs, maximumAge: 5 * 60 * 1000 },
    );
  });
}

/** "2.4 km" / "850 m" */
export function formatDistance(km: number): string {
  if (!Number.isFinite(km)) return '';
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`;
}

/** Turn a 0-1 match score into a whole-number percentage. */
export function formatScore(score: number): string {
  return `${Math.round(Math.max(0, Math.min(1, score)) * 100)}%`;
}

/** Keep only the last N turns so requests stay small. */
export function trimHistory(history: ConversationMessage[], maxTurns = 8): ConversationMessage[] {
  return history.slice(-maxTurns);
}

/** Pick the speech-recognition / synthesis locale for the app language. */
export function speechLocale(language: string): string {
  return language === 'hi' ? 'hi-IN' : 'en-IN'; // Hinglish is best recognised as en-IN
}

/** Only allow http(s) links from the backend/TinyFish before rendering them as <a href>. */
export function safeExternalUrl(url?: string | null): string | null {
  if (!url) return null;
  try {
    const u = new URL(url);
    return u.protocol === 'https:' || u.protocol === 'http:' ? u.toString() : null;
  } catch {
    return null;
  }
}
