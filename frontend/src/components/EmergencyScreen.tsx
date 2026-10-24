// frontend/src/components/EmergencyScreen.tsx
import { useEffect } from 'react';
import { TriageResponse, RedFlag } from '../types/api';

interface EmergencyScreenProps {
  response: TriageResponse;
  onRestart: () => void;
  language: string;
  t: (key: string) => string;
  textSize: number;
  speak: (text: string, lang: string) => void;
}

export function EmergencyScreen({ response, onRestart, language, t, textSize, speak }: EmergencyScreenProps) {
  useEffect(() => {
    // Auto-speak emergency instructions
    speak(t('emergency_auto_message'), language);
  }, []);

  const flagLabels: Record<RedFlag, string> = {
    chest_pain: 'chest_pain',
    breathlessness: 'breathlessness',
    unconsciousness: 'unconsciousness',
    severe_bleeding: 'severe_bleeding',
    stroke_symptoms: 'stroke_symptoms',
    seizure: 'seizure',
    high_fever_infant: 'high_fever_infant',
    suicidal_ideation: 'suicidal_ideation',
    severe_dehydration: 'severe_dehydration',
  };

  return (
    <div className="bg-red-50 border-4 border-red-500 rounded-2xl p-6 min-h-[400px] flex flex-col justify-center" role="alert">
      <div className="text-center mb-6">
        <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-red-700 mb-2">{t('emergency_title')}</h1>
        <p className="text-xl text-red-600">{t('emergency_subtitle')}</p>
      </div>

      {/* Call 112 Button */}
      <a 
        href="tel:112" 
        className="btn-emergency text-xl py-5 px-8 mb-6 text-center block"
        role="button"
      >
        📞 {t('call_112_now')}
      </a>

      {/* Detected Red Flags */}
      {response.red_flags.length > 0 && (
        <div className="bg-red-100 border border-red-200 rounded-xl p-4 mb-6 text-left">
          <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {t('detected_concerns')}
          </h3>
          <ul className="space-y-1">
            {response.red_flags.map((flag, idx) => (
              <li key={idx} className="text-red-700 flex items-center gap-2">
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                {t(flagLabels[flag] || flag)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Emergency Steps */}
      <div className="bg-white border border-red-200 rounded-xl p-4 mb-6 text-left">
        <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          {t('emergency_steps_title')}
        </h3>
        <ol className="space-y-3 text-red-700">
          {[
            'emergency_step_1',
            'emergency_step_2',
            'emergency_step_3',
          ].map((step, idx) => (
            <li key={idx} className="flex gap-3">
              <span className="flex-shrink-0 w-7 h-7 bg-red-500 text-white rounded-full flex items-center justify-center text-sm font-bold">{idx + 1}</span>
              <span>{t(step)}</span>
            </li>
          ))}
        </ol>
      </div>

      <p className="text-center text-red-600 text-sm mb-6">{t('emergency_disclaimer')}</p>

      <button
        onClick={onRestart}
        className="btn-secondary w-full py-3"
      >
        {t('start_over')}
      </button>
    </div>
  );
}