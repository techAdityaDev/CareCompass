# backend/app/data_loader.py
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import lru_cache
from app.config import get_settings

settings = get_settings()

# --- Care Taxonomy (from problem statement) ---
CARE_TAXONOMY = {
    "care_types": {
        "paramedic_home_visit": {
            "description": "Medic home visit for vitals, assessment, general complaints",
            "red_flags": ["chest_pain", "breathlessness", "unconsciousness", "severe_bleeding", 
                          "stroke_symptoms", "seizure", "high_fever_infant", "suicidal_ideation", 
                          "severe_dehydration"],
            "role_required": "medic",
            "skills": ["vitals_monitoring", "assessment", "elderly_care", "sample_collection"]
        },
        "home_nursing": {
            "description": "Nursing procedures: injections, dressing, IV, catheter, post-surgical",
            "red_flags": ["chest_pain", "breathlessness", "unconsciousness", "severe_bleeding",
                          "stroke_symptoms", "seizure", "high_fever_infant", "suicidal_ideation",
                          "severe_dehydration"],
            "role_required": "medic",
            "skills": ["injection_im", "injection_iv", "wound_dressing", "catheter_care", 
                       "post_surgical_care", "nebulization", "bp_sugar_check"]
        },
        "lab_test_home": {
            "description": "Home sample collection for diagnostic tests",
            "red_flags": [],
            "role_required": "phlebotomist",
            "skills": ["sample_collection", "home_phlebotomy"]
        },
        "teleconsultation": {
            "description": "Virtual doctor consultation",
            "red_flags": ["chest_pain", "breathlessness", "unconsciousness", "severe_bleeding",
                          "stroke_symptoms", "seizure", "high_fever_infant", "suicidal_ideation",
                          "severe_dehydration"],
            "role_required": "doctor",
            "skills": ["teleconsultation", "prescription", "report_review"]
        },
        "emergency_112": {
            "description": "Immediate emergency referral",
            "red_flags": ["chest_pain", "breathlessness", "unconsciousness", "severe_bleeding",
                          "stroke_symptoms", "seizure", "high_fever_infant", "suicidal_ideation",
                          "severe_dehydration"],
            "role_required": None,
            "skills": []
        }
    },
    "urgency_levels": {
        "emergency": "Immediate threat to life or limb",
        "same_day": "Needs attention within hours",
        "scheduled": "Can be scheduled for later"
    },
    "red_flag_definitions": {
        "chest_pain": "Severe chest pain, pressure, tightness",
        "breathlessness": "Difficulty breathing, shortness of breath, gasping",
        "unconsciousness": "Unresponsive, collapsed, not responding",
        "severe_bleeding": "Heavy bleeding that won't stop",
        "stroke_symptoms": "Facial droop, arm weakness, speech difficulty",
        "seizure": "Convulsions, fits, uncontrolled shaking",
        "high_fever_infant": "High fever in infant/young child",
        "suicidal_ideation": "Expressing desire to harm self or end life",
        "severe_dehydration": "Severe dehydration signs: no urine, sunken eyes, lethargy"
    }
}

@lru_cache(maxsize=1)
def load_training_data() -> pd.DataFrame:
    """Load flat CSV training data."""
    path = settings.DATA_DIR / "triage_dataset_flat.csv"
    if not path.exists():
        raise FileNotFoundError(f"Training data not found at {path}")
    df = pd.read_csv(path)
    return df

@lru_cache(maxsize=1)
def load_caregivers() -> pd.DataFrame:
    """Load caregiver profiles."""
    path = settings.DATA_DIR / "caregivers.csv"
    if not path.exists():
        raise FileNotFoundError(f"Caregiver data not found at {path}")
    df = pd.read_csv(path)
    # Parse semicolon-separated fields
    for col in ["languages", "skills"]:
        df[col] = df[col].fillna("").apply(lambda x: [s.strip() for s in x.split(";") if s.strip()])
    # Parse time strings
    for col in ["free_from", "free_until"]:
        df[col] = pd.to_datetime(df[col], format="%H:%M", errors="coerce").dt.time
    return df

@lru_cache(maxsize=1)
def load_multi_turn_examples() -> List[Dict]:
    """Load multi-turn conversation examples."""
    path = settings.DATA_DIR / "multi_turn_examples.jsonl"
    if not path.exists():
        return []
    examples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples

def get_red_flag_vocab() -> List[str]:
    """Get controlled red-flag vocabulary."""
    return [rf.value for rf in RedFlag]

def get_care_type_keywords() -> Dict[str, List[str]]:
    """Keywords mapping to care types for rule-based routing."""
    return {
        "home_nursing": [
            "injection", "dressing", "wound", "catheter", "iv", "intravenous",
            "insulin", "bp check", "blood pressure", "sugar check", "glucose",
            "post-surgical", "post surgical", "stitches", "suture"
        ],
        "lab_test_home": [
            "blood test", "lab test", "sample collection", "cbc", "thyroid",
            "blood sugar", "glucose test", "hba1c", "lipid", "kidney", "liver",
            "urine test", "stool test", "home collection", "phlebotomist"
        ],
        "teleconsultation": [
            "doctor", "consult", "advice", "second opinion", "prescription",
            "report review", "talk to doctor", "virtual", "video call", "acidity",
            "gas", "mild", "follow up", "medicine review"
        ],
        "paramedic_home_visit": [
            "fever", "cough", "cold", "weakness", "not eating", "lethargy",
            "body ache", "headache", "vomiting", "diarrhea", "checkup",
            "home visit", "medic", "assessment", "vitals", "bp sugar"
        ]
    }