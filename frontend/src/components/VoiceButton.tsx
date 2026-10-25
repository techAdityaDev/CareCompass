import { useState, useRef, useEffect } from 'react';

interface SpeechResult {
  isFinal: boolean;
  0: { transcript: string };
}

interface SpeechResultEvent extends Event {
  resultIndex: number;
  results: ArrayLike<SpeechResult>;
}

interface SpeechErrorEvent extends Event {
  error: string;
}

interface SpeechRecognitionLike {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onresult: ((event: SpeechResultEvent) => void) | null;
  onerror: ((event: SpeechErrorEvent) => void) | null;
  start: () => void;
  stop: () => void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

interface VoiceButtonProps {
  onVoiceInput: (transcript: string) => void;
  language: string;
  t: (key: string) => string;
}

export function VoiceButton({ onVoiceInput, language, t }: VoiceButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    const speechWindow = window as Window & {
      SpeechRecognition?: SpeechRecognitionConstructor;
      webkitSpeechRecognition?: SpeechRecognitionConstructor;
    };
    const SpeechRecognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = false;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
    
    recognitionRef.current.onstart = () => setIsListening(true);
    recognitionRef.current.onend = () => setIsListening(false);
    
    recognitionRef.current.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        setTranscript(finalTranscript);
        setShowConfirm(true);
      }
    };
    
    recognitionRef.current.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };
  }, [language]);

  const handleClick = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      setTranscript('');
      setShowConfirm(false);
      recognitionRef.current?.start();
    }
  };

  const handleConfirm = (confirmed: boolean) => {
    if (confirmed && transcript) onVoiceInput(transcript);
    setShowConfirm(false);
    setTranscript('');
  };

  if (showConfirm && transcript) {
    return (
      <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-xl p-3 min-w-[200px]">
        <p className="text-sm text-blue-800 flex-1 truncate">"{transcript}"</p>
        <div className="flex gap-1">
          <button
            onClick={() => handleConfirm(true)}
            className="btn-primary text-sm px-3 py-1"
          >
            {t('correct')}
          </button>
          <button
            onClick={() => handleConfirm(false)}
            className="btn-outline text-sm px-3 py-1"
          >
            {t('retry')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`btn-icon-round p-3 transition-all ${
        isListening 
          ? 'bg-red-100 text-red-600 ring-2 ring-red-200 animate-pulse' 
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
      aria-label={isListening ? t('stop_listening') : t('start_listening')}
      aria-pressed={isListening}
    >
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {isListening ? (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14v6m-3-3h6M6 10a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2a2 2 0 01-2 2h-2m-4-6a9 9 0 100 18 9 9 0 000-18z" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        )}
      </svg>
    </button>
  );
}