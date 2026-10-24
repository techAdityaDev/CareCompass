// frontend/src/App.tsx
import { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ChatInterface } from './components/ChatInterface';
import { EmergencyScreen } from './components/EmergencyScreen';
import { ResultScreen } from './components/ResultScreen';
import { BookingConfirm } from './components/BookingConfirm';
import { DoctorConsultCard } from './components/DoctorConsultCard';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { AccessibilityToggle } from './components/AccessibilityToggle';
import { useTriage } from './hooks/useTriage';
import { useI18n } from './hooks/useI18n';
import { useSpeech } from './hooks/useSpeech';
import { TriageResponse, CareType, Urgency, MatchedCaregiver } from './types/api';
import './index.css';

type AppState = 
  | { stage: 'welcome' }
  | { stage: 'language' }
  | { stage: 'chat'; response: TriageResponse | null }
  | { stage: 'emergency'; response: TriageResponse }
  | { stage: 'result'; response: TriageResponse }
  | { stage: 'booking'; caregiver: MatchedCaregiver; response: TriageResponse }
  | { stage: 'teleconsult'; response: TeleconsultResponse };

interface TeleconsultResponse {
  doctors: Array<{ doctor_id: string; name: string; language: string; rating: number; next_slot: string; profile_url?: string }>;
  fallback_used: boolean;
  message: string;
}

function App() {
  const { t, language, setLanguage } = useI18n();
  const { speak, stopSpeaking, isSupported: speechSupported } = useSpeech();
  const { triage, loading, error, reset } = useTriage();
  
  const [appState, setAppState] = useState<AppState>({ stage: 'welcome' });
  const [conversationHistory, setConversationHistory] = useState<Array<{role: 'user' | 'assistant', content: string}>>([]);
  const [followUpCount, setFollowUpCount] = useState(0);
  const [textSize, setTextSize] = useState(1);
  const [showAccessibility, setShowAccessibility] = useState(false);

  // Auto-speak assistant messages
  useEffect(() => {
    if (appState.stage === 'chat' && appState.response?.follow_up_question) {
      speak(appState.response.follow_up_question, language);
    } else if (appState.stage === 'result' && appState.response?.reasoning) {
      speak(`${t('care_needed')}: ${t(appState.response.care_type || '')}. ${t('urgency')}: ${t(appState.response.urgency || '')}. ${appState.response.reasoning}`, language);
    } else if (appState.stage === 'emergency') {
      speak(t('emergency_instruction'), language);
    }
  }, [appState, speak, language, t]);

  const handleUserInput = useCallback(async (input: string) => {
    if (!input.trim()) return;
    
    setConversationHistory(prev => [...prev, { role: 'user', content: input }]);
    
    try {
      const response = await triage({
        user_input: input,
        language: language === 'hinglish' ? 'hinglish' : language,
        location: { lat: 28.6139, lng: 77.2090 }, // Default Delhi
        conversation_history: conversationHistory.map(m => ({ role: m.role, content: m.content }))
      });
      
      if (response.follow_up_question) {
        setConversationHistory(prev => [...prev, { role: 'assistant', content: response.follow_up_question }]);
        setFollowUpCount(prev => prev + 1);
        setAppState({ stage: 'chat', response });
      } else if (response.care_type === CareType.EMERGENCY_112) {
        setAppState({ stage: 'emergency', response });
      } else {
        setAppState({ stage: 'result', response });
      }
    } catch (err) {
      console.error(err);
      // Fallback response
      const fallbackResponse: TriageResponse = {
        follow_up_question: null,
        care_type: CareType.PARAMEDIC_HOME_VISIT,
        urgency: Urgency.SAME_DAY,
        red_flags: [],
        reasoning: t('fallback_reasoning'),
        matched_caregivers: []
      };
      setAppState({ stage: 'result', response: fallbackResponse });
    }
  }, [triage, conversationHistory, language, t]);

  const handleQuickAction = (service: string) => {
    const prompts: Record<string, string> = {
      fever: language === 'hi' ? 'बुखार है' : language === 'hinglish' ? 'bukhar hai' : 'I have fever',
      injection: language === 'hi' ? 'इंजेक्शन लगवाना है' : language === 'hinglish' ? 'injection lagwana hai' : 'Need injection at home',
      lab: language === 'hi' ? 'खून की जांच घर पर' : language === 'hinglish' ? 'blood test ghar pe' : 'Blood test at home',
      doctor: language === 'hi' ? 'डॉक्टर से बात करनी है' : language === 'hinglish' ? 'doctor se baat karni hai' : 'Talk to a doctor',
      emergency: language === 'hi' ? 'इमरजेंसी है' : language === 'hinglish' ? 'emergency hai' : 'Emergency',
    };
    handleUserInput(prompts[service] || prompts.fever);
  };

  const handleVoiceInput = useCallback(async () => {
    if (!speechSupported) return;
    // Handled by VoiceButton component
  }, [speechSupported]);

  const handleBook = (caregiver: MatchedCaregiver, response: TriageResponse) => {
    setAppState({ stage: 'booking', caregiver, response });
  };

  const handleTeleconsult = async () => {
    setAppState({ stage: 'teleconsult', response: { doctors: [], fallback_used: false, message: 'Loading...' } });
    // In real app, call /api/v1/teleconsult
    // For demo, show fallback doctors
    const fallbackResponse: TeleconsultResponse = {
      doctors: [
        { doctor_id: 'CG_021', name: 'Dr. Rekha Gupta', language: 'Hindi, Tamil, Haryanvi', rating: 4.9, next_slot: 'Today 14:00 IST', profile_url: '#' },
        { doctor_id: 'CG_012', name: 'Dr. Kavita Das', language: 'Hindi, English', rating: 4.8, next_slot: 'Today 15:00 IST', profile_url: '#' },
        { doctor_id: 'CG_030', name: 'Dr. Pawan Singh', language: 'Hindi, Tamil, Bhojpuri', rating: 5.0, next_slot: 'Today 10:00 IST', profile_url: '#' },
      ],
      fallback_used: true,
      message: 'Showing available doctors from local network'
    };
    setAppState({ stage: 'teleconsult', response: fallbackResponse });
  };

  const handleRestart = () => {
    reset();
    setConversationHistory([]);
    setFollowUpCount(0);
    setAppState({ stage: 'welcome' });
    stopSpeaking();
  };

   // Render current stage
  const renderStage = () => {
    switch (appState.stage) {
      case 'welcome':
        return (
          <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
            <div className="w-24 h-24 bg-gradient-to-br from-teal-500 to-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-3">{t('app_name')}</h1>
            <p className="text-lg text-gray-600 mb-8 max-w-md">{t('welcome_subtitle')}</p>
            <div className="flex flex-col sm:flex-row gap-4 w-full max-w-md">
              <button
                onClick={() => setAppState({ stage: 'language' })}
                className="btn-primary text-lg py-4 px-6"
              >
                {t('get_started')}
              </button>
              <button
                onClick={() => setShowAccessibility(true)}
                className="btn-secondary text-lg py-4 px-6"
              >
                {t('accessibility_options')}
              </button>
            </div>
            <DisclaimerBanner />
          </div>
        );

      case 'language':
        return (
          <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('select_language')}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-md">
              {['en', 'hi', 'hinglish'].map(lang => (
                <button
                  key={lang}
                  onClick={() => { setLanguage(lang as any); setAppState({ stage: 'chat', response: null }); }}
                  className={`p-6 rounded-xl border-2 transition-all ${
                    language === lang 
                      ? 'border-teal-500 bg-teal-50 ring-2 ring-teal-200' 
                      : 'border-gray-200 hover:border-teal-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="text-4xl mb-2">
                    {lang === 'en' && '🇬🇧'}
                    {lang === 'hi' && '🇮🇳'}
                    {lang === 'hinglish' && '🇮🇳💬'}
                  </div>
                  <div className="font-semibold text-gray-900">{t(`lang_${lang}`)}</div>
                  <div className="text-sm text-gray-500 mt-1">{t(`lang_${lang}_desc`)}</div>
                </button>
              ))}
            </div>
            <button onClick={() => setAppState({ stage: 'welcome' })} className="mt-6 text-teal-600 hover:underline">
              {t('back')}
            </button>
          </div>
        );

      case 'chat':
        return (
          <ChatInterface
            response={appState.response}
            conversationHistory={conversationHistory}
            followUpCount={followUpCount}
            onUserInput={handleUserInput}
            onVoiceInput={handleVoiceInput}
            language={language}
            speechSupported={speechSupported}
            t={t}
            textSize={textSize}
          />
        );

      case 'emergency':
        return (
          <EmergencyScreen
            response={appState.response}
            onRestart={handleRestart}
            language={language}
            t={t}
            textSize={textSize}
            speak={speak}
          />
        );

      case 'result':
        return (
          <ResultScreen
            response={appState.response}
            onBook={handleBook}
            onTeleconsult={handleTeleconsult}
            onRestart={handleRestart}
            language={language}
            t={t}
            textSize={textSize}
            speak={speak}
          />
        );

      case 'booking':
        return (
          <BookingConfirm
            caregiver={appState.caregiver}
            response={appState.response}
            onConfirm={handleRestart}
            onBack={() => setAppState({ stage: 'result', response: appState.response })}
            language={language}
            t={t}
            textSize={textSize}
          />
        );

      case 'teleconsult':
        return (
          <DoctorConsultCard
            doctors={appState.response.doctors}
            fallbackUsed={appState.response.fallback_used}
            message={appState.response.message}
            onBack={() => setAppState({ stage: 'result', response: appState.response })}
            onRestart={handleRestart}
            language={language}
            t={t}
            textSize={textSize}
          />
        );
    }
  };

  return (
    <div className={`min-h-screen bg-gray-50 transition-all duration-300 ${textSize > 1 ? 'text-lg' : ''} ${textSize > 1.2 ? 'text-xl' : ''}`}>
      <Header 
        onRestart={handleRestart} 
        onAccessibilityClick={() => setShowAccessibility(true)}
        language={language}
        t={t}
        showBack={appState.stage !== 'welcome' && appState.stage !== 'language'}
      />
      
      <main className="flex-1 p-4 md:p-6">
        <div className="max-w-2xl mx-auto w-full">
          {renderStage()}
        </div>
      </main>

      <AccessibilityToggle
        isOpen={showAccessibility}
        onClose={() => setShowAccessibility(false)}
        textSize={textSize}
        onTextSizeChange={setTextSize}
        language={language}
        onLanguageChange={setLanguage}
        t={t}
      />

      <DisclaimerBanner />
    </div>
  );
}

export default App;