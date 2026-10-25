import { Language } from '../hooks/useI18n';

interface AccessibilityToggleProps {
  isOpen: boolean;
  onClose: () => void;
  textSize: number;
  onTextSizeChange: (size: number) => void;
  language: Language;
  onLanguageChange: (language: Language) => void;
  t: (key: string) => string;
}

export function AccessibilityToggle({ isOpen, onClose, textSize, onTextSizeChange, language, onLanguageChange, t }: AccessibilityToggleProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl" role="dialog" aria-modal="true" aria-labelledby="accessibility-title">
        <div className="mb-5 flex items-center justify-between">
          <h2 id="accessibility-title" className="text-xl font-bold text-gray-900">{t('accessibility_options')}</h2>
          <button onClick={onClose} className="rounded-lg px-3 py-2 text-gray-600 hover:bg-gray-100" aria-label={t('close')}>×</button>
        </div>
        <label className="mb-2 block font-medium text-gray-800" htmlFor="language-select">{t('select_language')}</label>
        <select id="language-select" value={language} onChange={(event) => onLanguageChange(event.target.value as Language)} className="mb-5 w-full rounded-xl border border-gray-300 p-3">
          <option value="en">{t('lang_en')}</option>
          <option value="hi">{t('lang_hi')}</option>
          <option value="hinglish">{t('lang_hinglish')}</option>
        </select>
        <p className="mb-2 font-medium text-gray-800">{t('text_size')}</p>
        <div className="grid grid-cols-3 gap-2">
          {[1, 1.15, 1.3].map((size) => (
            <button key={size} onClick={() => onTextSizeChange(size)} aria-pressed={textSize === size} className={`rounded-xl border p-3 ${textSize === size ? 'border-teal-600 bg-teal-50 text-teal-800' : 'border-gray-200'}`}>
              {size === 1 ? 'A' : size === 1.15 ? 'A+' : 'A++'}
            </button>
          ))}
        </div>
        <button onClick={onClose} className="btn-primary mt-6 w-full py-3">{t('close')}</button>
      </section>
    </div>
  );
}