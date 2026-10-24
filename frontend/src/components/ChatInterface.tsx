// frontend/src/components/ChatInterface.tsx
import { useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { FollowUpCard } from './FollowUpCard';
import { QuickActionTiles } from './QuickActionTiles';
import { VoiceButton } from './VoiceButton';
import { ProgressIndicator } from './ProgressIndicator';
import { TriageResponse } from '../types/api';

interface ChatInterfaceProps {
  response: TriageResponse | null;
  conversationHistory: Array<{role: 'user' | 'assistant', content: string}>;
  followUpCount: number;
  onUserInput: (input: string) => void;
  onVoiceInput: () => void;
  language: string;
  speechSupported: boolean;
  t: (key: string) => string;
  textSize: number;
}

export function ChatInterface({
  response,
  conversationHistory,
  followUpCount,
  onUserInput,
  onVoiceInput,
  language,
  speechSupported,
  t,
  textSize
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [inputValue, setInputValue] = useState('');
  const [showQuickActions, setShowQuickActions] = useState(conversationHistory.length === 0);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    inputRef.current?.focus();
  }, [conversationHistory, response]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    setShowQuickActions(false);
    onUserInput(inputValue);
    setInputValue('');
  };

  const handleQuickAction = (service: string) => {
    const prompts: Record<string, string> = {
      fever: language === 'hi' ? 'बुखार है' : language === 'hinglish' ? 'bukhar hai' : 'I have fever',
      injection: language === 'hi' ? 'इंजेक्शन लगवाना है' : language === 'hinglish' ? 'injection lagwana hai' : 'Need injection at home',
      lab: language === 'hi' ? 'खून की जांच घर पर' : language === 'hinglish' ? 'blood test ghar pe' : 'Blood test at home',
      doctor: language === 'hi' ? 'डॉक्टर से बात करनी है' : language === 'hinglish' ? 'doctor se baat karni hai' : 'Talk to a doctor',
      emergency: language === 'hi' ? 'इमरजेंसी है' : language === 'hinglish' ? 'emergency hai' : 'Emergency',
    };
    setShowQuickActions(false);
    onUserInput(prompts[service] || prompts.fever);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] min-h-[400px] bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Progress Indicator */}
      {response?.follow_up_question && (
        <ProgressIndicator current={followUpCount} max={3} t={t} />
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" role="log" aria-live="polite">
        {showQuickActions && (
          <QuickActionTiles onAction={handleQuickAction} language={language} t={t} />
        )}
        
        {conversationHistory.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} textSize={textSize} />
        ))}

        {response?.follow_up_question && (
          <FollowUpCard 
            question={response.follow_up_question} 
            language={language}
            t={t}
            textSize={textSize}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-100 bg-gray-50">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={t('type_or_speak')}
            rows={1}
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none min-h-[56px]"
            style={{ fontSize: `${16 * textSize}px` }}
            aria-label={t('type_or_speak')}
          />
          {speechSupported && (
            <VoiceButton onVoiceInput={onVoiceInput} language={language} t={t} />
          )}
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="btn-primary px-6 py-3 min-h-[56px] flex items-center justify-center"
            aria-label={t('send')}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-500 text-center mt-2">{t('privacy_note')}</p>
      </form>
    </div>
  );
}