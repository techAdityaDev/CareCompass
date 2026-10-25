// frontend/src/components/CaregiverCard.tsx
import { MatchedCaregiver, TriageResponse } from '../types/api';

interface CaregiverCardProps {
  caregiver: MatchedCaregiver;
  rank: number;
  onBook: (caregiver: MatchedCaregiver, response: TriageResponse) => void;
  response: TriageResponse;
  language: string;
  t: (key: string) => string;
  textSize: number;
}

export function CaregiverCard({ caregiver, rank, onBook, response, t }: CaregiverCardProps) {
  const initials = caregiver.caregiver_id.split('_')[1] || 'CG';
  
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        {/* Rank Badge */}
        <div className="flex-shrink-0 w-10 h-10 bg-teal-100 rounded-xl flex items-center justify-center">
          <span className="font-bold text-teal-700 text-lg">{rank}</span>
        </div>
        
        {/* Caregiver Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-teal-400 to-blue-500 rounded-xl flex items-center justify-center text-white font-bold">
              {initials}
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 truncate">{t('caregiver')}</h4>
              <p className="text-sm text-gray-500">{caregiver.caregiver_id}</p>
            </div>
            <span className={`ml-auto px-2 py-1 rounded-full text-xs font-medium ${
              rank === 1 ? 'bg-teal-100 text-teal-700' : 'bg-gray-100 text-gray-600'
            }`}>
              {rank === 1 ? t('best_match') : t('alternative')}
            </span>
          </div>
          
          {/* Match Reason */}
          <div className="bg-teal-50 border border-teal-100 rounded-lg p-3 mb-3">
            <p className="text-sm text-teal-800 flex items-start gap-1">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {caregiver.reason}
            </p>
          </div>
          
          {/* Score */}
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-teal-500 rounded-full transition-all duration-500"
                style={{ width: `${caregiver.score * 100}%` }}
              />
            </div>
            <span className="text-sm font-medium text-teal-600 w-12 text-right">
              {Math.round(caregiver.score * 100)}%
            </span>
          </div>
        </div>
      </div>
      
      {/* Book Button */}
      <button
        onClick={() => onBook(caregiver, response)}
        className={`w-full mt-4 py-3 rounded-xl font-semibold transition-all ${
          rank === 1 
            ? 'btn-primary text-lg' 
            : 'btn-outline'
        }`}
      >
        {rank === 1 ? t('book_now') : `${t('book_this_caregiver')}`}
      </button>
    </div>
  );
}