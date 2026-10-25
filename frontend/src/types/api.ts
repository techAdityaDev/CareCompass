// frontend/src/types/api.ts
export const CareType = {
  PARAMEDIC_HOME_VISIT: 'paramedic_home_visit',
  HOME_NURSING: 'home_nursing',
  LAB_TEST_HOME: 'lab_test_home',
  TELECONSULTATION: 'teleconsultation',
  EMERGENCY_112: 'emergency_112',
} as const;
export type CareType = (typeof CareType)[keyof typeof CareType];

export const Urgency = {
  EMERGENCY: 'emergency',
  SAME_DAY: 'same_day',
  SCHEDULED: 'scheduled',
} as const;
export type Urgency = (typeof Urgency)[keyof typeof Urgency];

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