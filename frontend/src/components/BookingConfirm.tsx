import { useState } from 'react';
import { MatchedCaregiver, TriageResponse } from '../types/api';

interface BookingConfirmProps {
  caregiver: MatchedCaregiver;
  response: TriageResponse;
  onConfirm: () => void;
  onBack: () => void;
  language: string;
  t: (key: string) => string;
  textSize: number;
}

interface BookingResult {
  booking_id: string;
  status: string;
  message: string;
  caregiver_name: string;
  estimated_arrival?: string;
}

export function BookingConfirm({ caregiver, onConfirm, onBack, t }: BookingConfirmProps) {
  const [result, setResult] = useState<BookingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const confirmBooking = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          caregiver_id: caregiver.caregiver_id,
          user_location: { lat: 28.6139, lng: 77.209 },
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setResult(await response.json() as BookingResult);
    } catch (bookingError) {
      setError(bookingError instanceof Error ? bookingError.message : t('booking_error'));
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <section className="rounded-2xl border border-teal-200 bg-white p-6 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-teal-100 text-2xl text-teal-700">✓</div>
        <h1 className="text-2xl font-bold text-gray-900">{t('booking_confirmed')}</h1>
        <p className="mt-3 text-gray-700">{result.message}</p>
        {result.estimated_arrival && <p className="mt-2 text-sm text-gray-600">{t('estimated_arrival')}: {result.estimated_arrival}</p>}
        <p className="mt-2 text-xs text-gray-500">{t('booking_id')}: {result.booking_id}</p>
        <button onClick={onConfirm} className="btn-primary mt-6 w-full py-3">{t('done')}</button>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-bold text-gray-900">{t('confirm_booking')}</h1>
      <p className="mt-3 text-gray-600">{t('caregiver')}: {caregiver.caregiver_id}</p>
      <p className="mt-2 text-sm text-gray-600">{caregiver.reason}</p>
      {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{t('booking_error')}: {error}</p>}
      <div className="mt-6 flex flex-col gap-3">
        <button onClick={() => void confirmBooking()} disabled={loading} className="btn-primary w-full py-3">
          {loading ? t('processing') : t('confirm_booking')}
        </button>
        <button onClick={onBack} disabled={loading} className="btn-outline w-full py-3">{t('back')}</button>
      </div>
    </section>
  );
}