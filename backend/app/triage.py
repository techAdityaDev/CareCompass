# backend/app/triage.py
"""
Module 2: Triage - Care type + urgency classification.
Hybrid: Rules for clear cases + ML for ambiguous.
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from app.schemas import CareType, Urgency, RedFlag
from app.utils import expand_hinglish, transliterate_if_needed, normalize_text, haversine_km
from app.data_loader import CARE_TAXONOMY, get_care_type_keywords
from app.config import get_settings
import joblib
from pathlib import Path

settings = get_settings()

@dataclass
class TriageResult:
    care_type: Optional[CareType]
    urgency: Optional[Urgency]
    reasoning: str
    confidence: float

# --- Rule-based routing (high precision for clear cases) ---
SERVICE_TO_CARE_TYPE = {
    "injection": CareType.HOME_NURSING,
    "dressing": CareType.HOME_NURSING,
    "lab_test": CareType.LAB_TEST_HOME,
    "consult": CareType.TELECONSULTATION,
    "vitals_check": CareType.PARAMEDIC_HOME_VISIT,
}

URGENCY_RULES = {
    CareType.EMERGENCY_112: Urgency.EMERGENCY,
    CareType.HOME_NURSING: Urgency.SAME_DAY,
    CareType.PARAMEDIC_HOME_VISIT: Urgency.SAME_DAY,
    CareType.LAB_TEST_HOME: Urgency.SCHEDULED,
    CareType.TELECONSULTATION: Urgency.SAME_DAY,
}

# Symptoms suggesting higher urgency
URGENT_SYMPTOMS = {
    "fever", "high fever", "severe pain", "chest pain", "breathlessness",
    "unconscious", "bleeding", "seizure", "stroke", "dehydration",
    "not eating", "lethargy", "weakness", "vomiting", "diarrhea"
}

def rule_based_triage(symptoms) -> Optional[TriageResult]:
    """Deterministic rules for clear-cut cases."""
    # Explicit service request
    if symptoms.requested_service and symptoms.requested_service in SERVICE_TO_CARE_TYPE:
        care_type = SERVICE_TO_CARE_TYPE[symptoms.requested_service]
        urgency = URGENCY_RULES[care_type]
        reason = f"Specific {symptoms.requested_service.replace('_', ' ')} requested"
        return TriageResult(care_type, urgency, reason, 0.95)
    
    # Symptom-based routing
    symptom_text = " ".join(symptoms.symptoms).lower()
    
    # Nursing procedures
    nursing_kws = ["injection", "dressing", "wound", "catheter", "iv", "insulin", "bp check", "sugar check"]
    if any(kw in symptom_text for kw in nursing_kws):
        return TriageResult(
            CareType.HOME_NURSING, Urgency.SAME_DAY,
            f"Nursing procedure indicated: {', '.join([k for k in nursing_kws if k in symptom_text])}",
            0.9
        )
    
    # Lab tests
    lab_kws = ["blood test", "lab test", "sample", "cbc", "thyroid", "hba1c", "glucose"]
    if any(kw in symptom_text for kw in lab_kws):
        return TriageResult(
            CareType.LAB_TEST_HOME, Urgency.SCHEDULED,
            f"Diagnostic test requested: {', '.join([k for k in lab_kws if k in symptom_text])}",
            0.9
        )
    
    # Teleconsultation triggers
    consult_kws = ["doctor", "consult", "advice", "second opinion", "acidity", "gas", "mild", "report", "prescription"]
    if any(kw in symptom_text for kw in consult_kws) and not any(kw in symptom_text for kw in URGENT_SYMPTOMS):
        return TriageResult(
            CareType.TELECONSULTATION, Urgency.SAME_DAY,
            "Non-urgent query suitable for virtual doctor consultation",
            0.85
        )
    
    # General symptoms -> paramedic visit
    general_kws = ["fever", "cough", "cold", "weakness", "body ache", "headache", "checkup", "vitals"]
    if any(kw in symptom_text for kw in general_kws):
        urgency = Urgency.SAME_DAY if any(kw in symptom_text for kw in URGENT_SYMPTOMS) else Urgency.SCHEDULED
        return TriageResult(
            CareType.PARAMEDIC_HOME_VISIT, urgency,
            f"General complaint suitable for Medic home visit",
            0.75
        )
    
    return None

# --- ML Classifier (TF-IDF + LightGBM) ---
class TriageClassifier:
    def __init__(self):
        self.vectorizer = None
        self.care_type_model = None
        self.urgency_model = None
        self.care_type_encoder = None
        self.urgency_encoder = None
        self._load_or_train()
    
    def _load_or_train(self):
        model_dir = settings.MODEL_DIR
        care_path = model_dir / "care_type_clf.joblib"
        urg_path = model_dir / "urgency_clf.joblib"
        vec_path = model_dir / "triage_tfidf.joblib"
        care_enc_path = model_dir / "care_type_enc.joblib"
        urg_enc_path = model_dir / "urgency_enc.joblib"
        
        if all(p.exists() for p in [care_path, urg_path, vec_path, care_enc_path, urg_enc_path]):
            self.care_type_model = joblib.load(care_path)
            self.urgency_model = joblib.load(urg_path)
            self.vectorizer = joblib.load(vec_path)
            self.care_type_encoder = joblib.load(care_enc_path)
            self.urgency_encoder = joblib.load(urg_enc_path)
        else:
            self._train()
            model_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.care_type_model, care_path)
            joblib.dump(self.urgency_model, urg_path)
            joblib.dump(self.vectorizer, vec_path)
            joblib.dump(self.care_type_encoder, care_enc_path)
            joblib.dump(self.urgency_encoder, urg_enc_path)
    
    def _train(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from lightgbm import LGBMClassifier
        from sklearn.preprocessing import LabelEncoder
        from app.data_loader import load_training_data
        from app.utils import expand_hinglish, transliterate_if_needed, normalize_text
        import pandas as pd
        
        df = load_training_data()
        # Only use rows with definitive labels
        df_labeled = df[df["care_type"].notna()].copy()
        
        texts = df_labeled["user_input"].apply(
            lambda x: expand_hinglish(transliterate_if_needed(normalize_text(str(x))))
        ).tolist()
        
        # Labels
        y_care = df_labeled["care_type"].tolist()
        y_urg = df_labeled["urgency"].fillna("same_day").tolist()
        
        self.care_type_encoder = LabelEncoder()
        self.urgency_encoder = LabelEncoder()
        y_care_enc = self.care_type_encoder.fit_transform(y_care)
        y_urg_enc = self.urgency_encoder.fit_transform(y_urg)
        
        # TF-IDF char n-grams
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 6), max_features=8000,
            sublinear_tf=True, min_df=2
        )
        X = self.vectorizer.fit_transform(texts)
        
        # Care type classifier
        self.care_type_model = LGBMClassifier(
            n_estimators=300, max_depth=8, learning_rate=0.05,
            class_weight="balanced", verbosity=-1, random_state=42,
            objective="multiclass", metric="multi_logloss"
        )
        self.care_type_model.fit(X, y_care_enc)
        
        # Urgency classifier
        self.urgency_model = LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            class_weight="balanced", verbosity=-1, random_state=42,
            objective="multiclass", metric="multi_logloss"
        )
        self.urgency_model.fit(X, y_urg_enc)
    
    def predict(self, text: str) -> Tuple[CareType, Urgency, float, float]:
        from app.utils import expand_hinglish, transliterate_if_needed, normalize_text
        normalized = expand_hinglish(transliterate_if_needed(normalize_text(text)))
        X = self.vectorizer.transform([normalized])
        
        care_proba = self.care_type_model.predict_proba(X)[0]
        care_idx = care_proba.argmax()
        care_conf = care_proba.max()
        care_type = CareType(self.care_type_encoder.inverse_transform([care_idx])[0])
        
        urg_proba = self.urgency_model.predict_proba(X)[0]
        urg_idx = urg_proba.argmax()
        urg_conf = urg_proba.max()
        urgency = Urgency(self.urgency_encoder.inverse_transform([urg_idx])[0])
        
        return care_type, urgency, care_conf, urg_conf

# Singleton
_triage_clf = None
def get_triage_classifier() -> TriageClassifier:
    global _triage_clf
    if _triage_clf is None:
        _triage_clf = TriageClassifier()
    return _triage_clf

# --- Main Triage Function ---
def triage(symptoms, red_flags: List[RedFlag]) -> TriageResult:
    # Emergency already handled by safety gate
    if red_flags:
        return TriageResult(
            CareType.EMERGENCY_112, Urgency.EMERGENCY,
            "Red-flag symptoms detected; immediate emergency referral.",
            1.0
        )
    
    # Try rules first
    rule_result = rule_based_triage(symptoms)
    if rule_result and rule_result.confidence >= 0.8:
        return rule_result
    
    # Fall back to ML
    clf = get_triage_classifier()
    # Combine all text for classification
    full_text = " ".join(filter(None, [
        symptoms.patient_relation or "",
        symptoms.age_group or "",
        " ".join(symptoms.symptoms),
        symptoms.duration or "",
        symptoms.requested_service or "",
    ]))
    
    care_type, urgency, care_conf, urg_conf = clf.predict(full_text)
    confidence = (care_conf + urg_conf) / 2
    
    # Asymmetric: if torn, pick more urgent
    if urgency == Urgency.SCHEDULED and care_conf < 0.7:
        urgency = Urgency.SAME_DAY
    
    # Generate reasoning
    reason_parts = []
    if symptoms.requested_service:
        reason_parts.append(f"{symptoms.requested_service.replace('_', ' ')} requested")
    if symptoms.symptoms:
        reason_parts.append(f"symptoms: {', '.join(symptoms.symptoms[:3])}")
    if symptoms.duration:
        reason_parts.append(f"duration: {symptoms.duration}")
    if symptoms.patient_relation:
        reason_parts.append(f"for {symptoms.patient_relation}")
    
    reasoning = "; ".join(reason_parts) if reason_parts else "General assessment"
    reasoning += f". Routed to {care_type.value.replace('_', ' ')} with {urgency.value} urgency."
    
    return TriageResult(care_type, urgency, reasoning, confidence)