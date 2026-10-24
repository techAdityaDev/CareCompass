// frontend/src/types/api.ts
export type CareType = 
  | 'paramedic_home_visit'
  | 'home_nursing'
  | 'lab_test_home'
  | 'teleconsultation'
  | 'emergency_112';

export type Urgency = 'emergency' | 'same_day' | 'scheduled';

export type RedFlag = 
  | 'chest_pain'
  | 'breathlessness'
  | 'unconsciousness'
  | 'severe_bleeding'
  | 'stroke_symptoms'
  | 'seizure'
  | 'high_fever_infant'
  | 'suicidal_ideation'
  | 'severe_dehydration';

export interface Location {
  lat: number;
  lng: number;
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface TriageRequest {
  user_input: string;
  language: 'auto' | 'en' | 'hi' | 'hinglish';
  location?: Location;
  conversation_history: ConversationMessage[];
}

export interface MatchedCaregiver {
  caregiver_id: string;
  score: number;
  reason: string;
}

export interface TriageResponse {
  follow_up_question: string | null;
  care_type: CareType | null;
  urgency: Urgency | null;
  red_flags: RedFlag[];
  reasoning: string;
  matched_caregivers: MatchedCaregiver[];
}