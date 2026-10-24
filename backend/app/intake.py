# backend/app/intake.py
"""
Module 1: Smart Intake - Extract structured symptoms, decide follow-up.
"""
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from app.utils import normalize_text, expand_hinglish, transliterate_if_needed, detect_script
from app.schemas import ConversationMessage, CareType, Urgency
from app.data_loader import get_care_type_keywords

@dataclass
class StructuredSymptoms:
    patient_relation: Optional[str] = None      # self, father, mother, child, etc.
    age_group: Optional[str] = None             # infant, child, adult, elderly
    symptoms: List[str] = field(default_factory=list)
    duration: Optional[str] = None              # "2 days", "since morning"
    severity: Optional[str] = None              # mild, moderate, severe
    requested_service: Optional[str] = None     # injection, dressing, lab, consult
    language: str = "en"
    confidence: float = 0.0

# --- Relation & Age Keywords ---
RELATION_KEYWORDS = {
    "self": ["myself", "me", "mujhe", "mere", "main"],
    "father": ["father", "papa", "dad", "pita", "baap"],
    "mother": ["mother", "mummy", "mom", "maa", "ma"],
    "child": ["child", "son", "daughter", "baccha", "bachcha", "beta", "beti", "kid"],
    "grandmother": ["grandmother", "dadi", "nani"],
    "grandfather": ["grandfather", "dada", "nana"],
    "spouse": ["wife", "husband", "patni", "pati", "spouse"],
    "other": ["patient", "relative", "family"],
}

AGE_KEYWORDS = {
    "infant": ["infant", "newborn", "baby", "bachcha", "shishu", "navjaat", "month old"],
    "child": ["child", "kid", "boy", "girl", "bachcha", "bachchi", "year old"],
    "elderly": ["elderly", "senior", "old", "aged", "grandfather", "grandmother", "dada", "dadi", "nana", "nani"],
}

SERVICE_KEYWORDS = {
    "injection": ["injection", "inject", "shot", "needle", "insulin", "iv", "intravenous", "im injection"],
    "dressing": ["dressing", "wound", "bandage", "stitches", "suture", "patti", "patti badal", "post-surgical", "post surgical"],
    "lab_test": ["blood test", "lab test", "sample", "collection", "cbc", "thyroid", "hba1c", "lipid", "blood sugar", "glucose", "urine", "stool", "phlebotomist"],
    "consult": ["doctor", "consult", "advice", "second opinion", "talk to doctor", "video call", "virtual", "prescription", "report review", "acidity", "gas", "mild"],
    "vitals_check": ["bp", "blood pressure", "sugar", "glucose", "vitals", "checkup", "check up", "monitoring"],
}

def extract_structured(text: str, conversation_history: List[ConversationMessage] = None) -> StructuredSymptoms:
    """Extract structured information from free text + history."""
    full_text = text
    if conversation_history:
        full_text = " ".join([msg.content for msg in conversation_history[-3:]] + [text])
    
    normalized = expand_hinglish(transliterate_if_needed(normalize_text(full_text)))
    script = detect_script(full_text)
    lang = "hi" if script == "devanagari" else ("hinglish" if script == "mixed" else "en")
    
    result = StructuredSymptoms(language=lang)
    
    # Relation
    for relation, keywords in RELATION_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            result.patient_relation = relation
            break
    
    # Age group
    for age, keywords in AGE_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            result.age_group = age
            break
    
    # Requested service
    for service, keywords in SERVICE_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            result.requested_service = service
            break
    
    # Symptoms (from care type keywords)
    care_keywords = get_care_type_keywords()
    for care_type, keywords in care_keywords.items():
        for kw in keywords:
            if kw in normalized:
                result.symptoms.append(kw)
    
    # Duration patterns
    import re
    duration_patterns = [
        r"(?:for|since)\s+(\d+\s*(?:day|days|hour|hours|week|weeks|month|months))",
        r"(\d+\s*(?:din|ghante|hafte|mahine))\s*(?:se|pehle)",
        r"(?:kal|aaj|parson|subah|shaam|raat)",
    ]
    for pattern in duration_patterns:
        match = re.search(pattern, normalized)
        if match:
            result.duration = match.group(1) if match.groups() else match.group(0)
            break
    
    # Severity
    if any(w in normalized for w in ["severe", "bad", "teez", "bahut", "extreme", "critical"]):
        result.severity = "severe"
    elif any(w in normalized for w in ["mild", "slight", "thoda", "kam", "little"]):
        result.severity = "mild"
    else:
        result.severity = "moderate"
    
    # Confidence heuristic
    info_count = sum([
        result.patient_relation is not None,
        result.age_group is not None,
        len(result.symptoms) > 0,
        result.duration is not None,
        result.requested_service is not None,
    ])
    result.confidence = min(0.3 + info_count * 0.15, 1.0)
    
    return result

# --- Follow-up Question Generator ---
FOLLOW_UP_QUESTIONS = {
    # Safety-first questions (asked first if unknown)
    "breathing": {
        "en": "Is there any difficulty in breathing or shortness of breath?",
        "hi": "क्या सांस लेने में तकलीफ है?",
        "hinglish": "Kya saans lene mein dikkat hai?",
        "buttons": [("Yes/Haan", "yes"), ("No/Nahi", "no")],
        "targets": ["breathlessness"],
    },
    "chest_pain": {
        "en": "Is there any chest pain, tightness, or discomfort?",
        "hi": "क्या सीने में दर्द या जकड़न है?",
        "hinglish": "Kya seene mein dard ya jakdan hai?",
        "buttons": [("Yes/Haan", "yes"), ("No/Nahi", "no")],
        "targets": ["chest_pain"],
    },
    "consciousness": {
        "en": "Is the person fully conscious and responding normally?",
        "hi": "क्या व्यक्ति पूरी तरह होश में है और जवाब दे रहे हैं?",
        "hinglish": "Kya person poori tarah hosh mein hai aur jawab de rahe hain?",
        "buttons": [("Yes/Haan", "yes"), ("No/Nahi", "no")],
        "targets": ["unconsciousness"],
    },
    "bleeding": {
        "en": "Is there any heavy bleeding that won't stop?",
        "hi": "क्या भारी खून बह रहा है जो रुक नहीं रहा?",
        "hinglish": "Kya bhaari khoon bah raha hai jo ruk nahi raha?",
        "buttons": [("Yes/Haan", "yes"), ("No/Nahi", "no")],
        "targets": ["severe_bleeding"],
    },
    # Service clarification
    "service_type": {
        "en": "What do you need help with — a home visit, nursing care, lab test, or doctor consultation?",
        "hi": "आपको किसमें मदद चाहिए — घर पर विजिट, नर्सिंग, लैब टेस्ट, या डॉक्टर से सलाह?",
        "hinglish": "Aapko kya chahiye — ghar pe visit, nursing, lab test, ya doctor consultation?",
        "buttons": [
            ("Home Visit", "paramedic_home_visit"),
            ("Nursing/Injection", "home_nursing"),
            ("Lab Test", "lab_test_home"),
            ("Doctor Consult", "teleconsultation"),
        ],
        "targets": ["requested_service"],
    },
    "duration": {
        "en": "How long has this been going on?",
        "hi": "यह कब से चल रहा है?",
        "hinglish": "Ye kab se chal raha hai?",
        "buttons": [
            ("< 1 hour", "<1h"),
            ("Few hours", "few_hours"),
            ("1-2 days", "1-2d"),
            ("3+ days", "3+d"),
        ],
        "targets": ["duration"],
    },
    "patient_identity": {
        "en": "Who is this for?",
        "hi": "यह किसके लिए है?",
        "hinglish": "Ye kiske liye hai?",
        "buttons": [
            ("Myself", "self"),
            ("Father", "father"),
            ("Mother", "mother"),
            ("Child", "child"),
            ("Other", "other"),
        ],
        "targets": ["patient_relation"],
    },
}

def select_follow_up(symptoms: StructuredSymptoms, conversation_history: List[ConversationMessage] = None) -> Optional[Dict]:
    """
    Select the single most important follow-up question.
    Priority: safety unknowns > service type > duration > patient identity.
    """
    # Track what we already know
    known = {
        "breathlessness": "breathlessness" in symptoms.symptoms,
        "chest_pain": "chest_pain" in symptoms.symptoms,
        "unconsciousness": "unconsciousness" in symptoms.symptoms,
        "severe_bleeding": "severe_bleeding" in symptoms.symptoms,
        "requested_service": symptoms.requested_service is not None,
        "duration": symptoms.duration is not None,
        "patient_relation": symptoms.patient_relation is not None,
    }
    
    # Check history for already-asked questions
    asked_targets = set()
    if conversation_history:
        for msg in conversation_history:
            if msg.role.value == "assistant":
                for q_key, q_data in FOLLOW_UP_QUESTIONS.items():
                    if any(t in msg.content.lower() for t in q_data.get("targets", [])):
                        asked_targets.update(q_data["targets"])
    
    # Priority order
    priority = [
        ("breathing", "breathlessness"),
        ("chest_pain", "chest_pain"),
        ("consciousness", "unconsciousness"),
        ("bleeding", "severe_bleeding"),
        ("service_type", "requested_service"),
        ("duration", "duration"),
        ("patient_identity", "patient_relation"),
    ]
    
    for q_key, target in priority:
        if not known.get(target, False) and target not in asked_targets:
            q = FOLLOW_UP_QUESTIONS[q_key].copy()
            q["key"] = q_key
            return q
    
    return None

def should_ask_follow_up(symptoms: StructuredSymptoms, follow_up_count: int) -> bool:
    """Decide if we need more info. Max 3 follow-ups; prefer 0-1."""
    if follow_up_count >= 3:
        return False
    if symptoms.confidence >= 0.8:
        return False
    # Always ask if service type unknown
    if not symptoms.requested_service and len(symptoms.symptoms) == 0:
        return True
    return symptoms.confidence < 0.6