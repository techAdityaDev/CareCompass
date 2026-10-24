# backend/app/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal, Dict, Any
from enum import Enum

# --- Enums (exact from problem statement) ---
class CareType(str, Enum):
    PARAMEDIC_HOME_VISIT = "paramedic_home_visit"
    HOME_NURSING = "home_nursing"
    LAB_TEST_HOME = "lab_test_home"
    TELECONSULTATION = "teleconsultation"
    EMERGENCY_112 = "emergency_112"

class Urgency(str, Enum):
    EMERGENCY = "emergency"
    SAME_DAY = "same_day"
    SCHEDULED = "scheduled"

class RedFlag(str, Enum):
    CHEST_PAIN = "chest_pain"
    BREATHLESSNESS = "breathlessness"
    UNCONSCIOUSNESS = "unconsciousness"
    SEVERE_BLEEDING = "severe_bleeding"
    STROKE_SYMPTOMS = "stroke_symptoms"
    SEIZURE = "seizure"
    HIGH_FEVER_INFANT = "high_fever_infant"
    SUICIDAL_IDEATION = "suicidal_ideation"
    SEVERE_DEHYDRATION = "severe_dehydration"

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

# --- Request/Response Models ---
class Location(BaseModel):
    lat: float
    lng: float

class ConversationMessage(BaseModel):
    role: Role
    content: str

class TriageRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=2000)
    language: Literal["auto", "en", "hi", "hinglish"] = "auto"
    location: Optional[Location] = None
    conversation_history: List[ConversationMessage] = Field(default_factory=list)

class MatchedCaregiver(BaseModel):
    caregiver_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str

class TriageResponse(BaseModel):
    follow_up_question: Optional[str] = None
    care_type: Optional[CareType] = None
    urgency: Optional[Urgency] = None
    red_flags: List[RedFlag] = Field(default_factory=list)
    reasoning: str
    matched_caregivers: List[MatchedCaregiver] = Field(default_factory=list)
    
    @field_validator("red_flags", mode="before")
    @classmethod
    def parse_red_flags(cls, v):
        if isinstance(v, str):
            return [RedFlag(x.strip()) for x in v.split(";") if x.strip()]
        return v

# --- Batch Predict ---
class BatchPredictRequest(BaseModel):
    csv_content: str  # base64 encoded or raw CSV text

class BatchPredictResponse(BaseModel):
    predictions_csv: str
    processed_count: int

# --- Booking ---
class BookingRequest(BaseModel):
    caregiver_id: str
    user_location: Location
    preferred_time: Optional[str] = None  # ISO format
    contact_phone: Optional[str] = None

class BookingResponse(BaseModel):
    booking_id: str
    status: Literal["confirmed", "pending", "failed"]
    message: str
    caregiver_name: str
    estimated_arrival: Optional[str] = None

# --- Teleconsult (TinyFish) ---
class TeleconsultRequest(BaseModel):
    language: Literal["en", "hi", "hinglish"] = "en"
    specialty: Optional[str] = None
    preferred_time: Optional[str] = None

class DoctorSlot(BaseModel):
    doctor_id: str
    name: str
    language: str
    rating: float
    next_slot: str  # ISO datetime
    profile_url: Optional[str] = None

class TeleconsultResponse(BaseModel):
    doctors: List[DoctorSlot]
    fallback_used: bool
    message: str

# --- Health ---
class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    models_loaded: bool
    data_loaded: bool