interface QuickActionTilesProps {
  onAction: (service: string) => void;
  language: string;
  t: (key: string) => string;
}

const actions = [
  { id: 'fever', label: 'quick_fever', icon: '🌡️' },
  { id: 'injection', label: 'quick_nursing', icon: '🩹' },
  { id: 'lab', label: 'quick_lab', icon: '🧪' },
  { id: 'doctor', label: 'quick_doctor', icon: '👩‍⚕️' },
  { id: 'emergency', label: 'quick_emergency', icon: '🚨' },
];

export function QuickActionTiles({ onAction, t }: QuickActionTilesProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600">{t('quick_actions')}</p>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {actions.map((action) => (
          <button key={action.id} type="button" onClick={() => onAction(action.id)} className="flex min-h-14 items-center gap-2 rounded-xl border border-gray-200 bg-white p-3 text-left text-sm font-medium text-gray-700 hover:border-teal-300 hover:bg-teal-50">
            <span aria-hidden="true">{action.icon}</span>
            {t(action.label)}
          </button>
        ))}
      </div>
    </div>
  );
}