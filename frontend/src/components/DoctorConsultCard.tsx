interface Doctor {
  doctor_id: string;
  name: string;
  language: string;
  rating: number;
  next_slot: string;
  profile_url?: string;
}

interface DoctorConsultCardProps {
  doctors: Doctor[];
  fallbackUsed: boolean;
  message: string;
  onBack: () => void;
  onRestart: () => void;
  language: string;
  t: (key: string) => string;
  textSize: number;
}

export function DoctorConsultCard({ doctors, fallbackUsed, message, onBack, onRestart, t }: DoctorConsultCardProps) {
  return (
    <section className="space-y-4">
      <div className="rounded-2xl border border-teal-100 bg-white p-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('talk_to_doctor')}</h1>
        <p className="mt-2 text-sm text-gray-600">{message}</p>
        {fallbackUsed && <p className="mt-2 text-xs text-gray-500">{t('local_network_notice')}</p>}
      </div>
      {doctors.length ? doctors.map((doctor) => (
        <article key={doctor.doctor_id} className="rounded-xl border border-gray-200 bg-white p-4">
          <h2 className="font-semibold text-gray-900">{doctor.name}</h2>
          <p className="mt-1 text-sm text-gray-600">{doctor.language}</p>
          <p className="mt-1 text-sm text-gray-600">★ {doctor.rating.toFixed(1)} · {doctor.next_slot}</p>
          {doctor.profile_url && doctor.profile_url !== '#' && (
            <a href={doctor.profile_url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm font-semibold text-teal-700 underline">{t('view_profile')}</a>
          )}
        </article>
      )) : <p className="rounded-xl bg-gray-50 p-5 text-gray-600">{t('no_doctors_found')}</p>}
      <div className="flex gap-3">
        <button onClick={onBack} className="btn-outline flex-1 py-3">{t('back')}</button>
        <button onClick={onRestart} className="btn-primary flex-1 py-3">{t('new_request')}</button>
      </div>
    </section>
  );
}