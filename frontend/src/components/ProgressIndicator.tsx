interface ProgressIndicatorProps {
  current: number;
  max: number;
  t: (key: string) => string;
}

export function ProgressIndicator({ current, max, t }: ProgressIndicatorProps) {
  return (
    <div className="border-b border-gray-100 px-4 py-3">
      <div className="mb-2 flex justify-between text-xs text-gray-500">
        <span>{t('intake_progress')}</span>
        <span>{Math.min(current, max)} / {max}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-gray-100">
        <div className="h-full rounded-full bg-teal-500 transition-all" style={{ width: `${Math.min((current / max) * 100, 100)}%` }} />
      </div>
    </div>
  );
}