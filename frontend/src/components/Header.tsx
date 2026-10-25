interface HeaderProps {
  onRestart: () => void;
  onAccessibilityClick: () => void;
  language: string;
  t: (key: string) => string;
  showBack: boolean;
}

export function Header({ onRestart, onAccessibilityClick, t, showBack }: HeaderProps) {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <button onClick={onRestart} className="flex items-center gap-3 text-left" aria-label={t('app_name')}>
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-600 text-lg font-bold text-white">C</span>
          <span className="text-lg font-bold text-gray-900">{t('app_name')}</span>
        </button>
        <div className="flex items-center gap-2">
          {showBack && (
            <button onClick={onRestart} className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100">
              {t('start_over')}
            </button>
          )}
          <button onClick={onAccessibilityClick} className="rounded-lg px-3 py-2 text-sm font-medium text-teal-700 hover:bg-teal-50">
            {t('accessibility_options')}
          </button>
        </div>
      </div>
    </header>
  );
}