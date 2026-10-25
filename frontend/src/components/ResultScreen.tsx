// frontend/src/components/ResultScreen.tsx
import { TriageResponse, CareType, Urgency, MatchedCaregiver } from '../types/api';
import { CaregiverCard } from './CaregiverCard';

interface ResultScreenProps {
  response: TriageResponse;
  onBook: (caregiver: MatchedCaregiver, response: TriageResponse) => void;
  onTeleconsult: () => void;
  onRestart: () => void;
  language: string;
  t: (key: string) => string;
  textSize: number;
  speak: (text: string, lang: string) => void;
}

const careTypeLabels: Record<CareType, string> = {
  paramedic_home_visit: 'paramedic_home_visit',
  home_nursing: 'home_nursing',
  lab_test_home: 'lab_test_home',
  teleconsultation: 'teleconsultation',
  emergency_112: 'emergency_112',
};

const urgencyLabels: Record<Urgency, string> = {
  emergency: 'emergency',
  same_day: 'same_day',
  scheduled: 'scheduled',
};

export function ResultScreen({ response, onBook, onTeleconsult, onRestart, language, t, textSize }: ResultScreenProps) {
  return (
    <div className="space-y-4">
      {/* Result Summary Card */}
      <div className="bg-gradient-to-r from-teal-50 to-blue-50 border border-teal-200 rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 bg-teal-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <svg className="w-7 h-7 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900">{t('care_recommendation')}</h2>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="px-3 py-1 bg-teal-100 text-teal-800 rounded-full text-sm font-medium">
                {response.care_type ? t(careTypeLabels[response.care_type]) : ''}
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                response.urgency === Urgency.EMERGENCY ? 'bg-red-100 text-red-800' :
                response.urgency === Urgency.SAME_DAY ? 'bg-orange-100 text-orange-800' :
                'bg-green-100 text-green-800'
              }`}>
                {response.urgency ? t(urgencyLabels[response.urgency]) : ''}
              </span>
            </div>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-white rounded-xl border border-gray-100">
          <p className="text-gray-700">{response.reasoning}</p>
        </div>
      </div>

      {/* Why This? Expandable */}
      <details className="group bg-white border border-gray-200 rounded-xl overflow-hidden">
        <summary className="p-4 flex items-center justify-between cursor-pointer list-none">
          <span className="font-medium text-gray-700 flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {t('why_this')}
          </span>
          <svg className="w-5 h-5 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div className="px-4 pb-4 border-t border-gray-100 text-sm text-gray-600">
          <p>{response.reasoning}</p>
          {response.matched_caregivers.length > 0 && (
            <p className="mt-2">{t('match_explanation')}</p>
          )}
        </div>
      </details>

      {/* Caregiver Matches */}
      {response.matched_caregivers.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            {t('available_caregivers')}
          </h3>
          {response.matched_caregivers.map((caregiver, idx) => (
            <CaregiverCard
              key={caregiver.caregiver_id}
              caregiver={caregiver}
              rank={idx + 1}
              onBook={onBook}
              response={response}
              language={language}
              t={t}
              textSize={textSize}
            />
          ))}
        </div>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-600">{t('no_caregivers_found')}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-3 pt-2">
        {response.care_type === CareType.TELECONSULTATION && (
          <button
            onClick={onTeleconsult}
            className="btn-secondary w-full py-4 text-lg flex items-center justify-center gap-2"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            {t('talk_to_doctor')}
          </button>
        )}
        <button
          onClick={onRestart}
          className="btn-outline w-full py-3"
        >
          {t('new_request')}
        </button>
      </div>
    </div>
  );
}