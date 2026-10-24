# backend/app/utils.py
import re
import unicodedata
from math import radians, sin, cos, sqrt, atan2
from typing import List, Set, Tuple
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from langdetect import detect, LangDetectException
from rapidfuzz import fuzz, process

# --- Text Normalization ---
HINGLISH_SYNONYMS = {
    # Symptoms
    "bukhar": "fever", "tap": "fever", "jor": "fever",
    "khansi": "cough", "kaali khansi": "dry cough",
    "saans phoolna": "breathlessness", "saans nahi aa rahi": "breathlessness",
    "dam ghutna": "breathlessness", "saans lene mein dikkat": "breathlessness",
    "seene mein dard": "chest pain", "chati mein dard": "chest pain",
    "dil mein dard": "chest pain", "heart pain": "chest pain",
    "behosh": "unconscious", "behoshi": "unconsciousness",
    "gir gaye": "fallen", "response nahi de rahe": "unresponsive",
    "bol nahi pa rahe": "unable to speak", "munh tedha": "facial droop",
    " khoon": "bleeding", "bleeding ruk nahi rahi": "severe bleeding",
    "daura": "seizure", "mirgi": "seizure", "fits": "seizure",
    "bachche ka tez bukhar": "high fever infant", "baby high fever": "high fever infant",
    "khudkushi": "suicidal", "marna chahte hain": "suicidal",
    "dehydration": "dehydration", "pani ki kami": "dehydration",
    # Actions
    "injection lagwana": "injection", "injection chahiye": "injection",
    "dressing karwana": "dressing", "patti badalwana": "dressing",
    "blood test": "blood test", "sample lena": "lab test",
    "doctor se baat": "teleconsult", "doctor chahiye": "teleconsult",
    "checkup": "checkup", "check up": "checkup",
    "bp check": "bp check", "sugar check": "sugar check",
    # Relations
    "papa": "father", "mummy": "mother", "dadi": "grandmother",
    "dada": "grandfather", "baccha": "child", "beta": "son", "beti": "daughter",
    "patni": "wife", "pati": "husband",
    # Urgency
    "turant": "immediate", "jaldi": "urgent", "emergency": "emergency",
    "kal": "tomorrow", "aaj": "today",
}

NEGATION_PATTERNS = [
    r"\b(no|not|nahi|nahin|na|without|koi nahi|kuch nahi)\b",
    r"\b(koi dikkat nahi|koi problem nahi|theek hoon|theek hai)\b",
]

def normalize_text(text: str) -> str:
    """Normalize unicode, lowercase, strip extra spaces."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def detect_script(text: str) -> str:
    """Detect script: devanagari, latin, mixed."""
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    total = devanagari + latin
    if total == 0:
        return "unknown"
    if devanagari / total > 0.5:
        return "devanagari"
    if latin / total > 0.5:
        return "latin"
    return "mixed"

def transliterate_if_needed(text: str) -> str:
    """Convert Devanagari Hindi to Roman for keyword matching."""
    script = detect_script(text)
    if script == "devanagari":
        try:
            return transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS).lower()
        except Exception:
            pass
    return text.lower()

def expand_hinglish(text: str) -> str:
    """Replace Hinglish synonyms with canonical English terms."""
    text_lower = text.lower()
    for hinglish, canonical in HINGLISH_SYNONYMS.items():
        text_lower = re.sub(rf"\b{re.escape(hinglish)}\b", canonical, text_lower)
    return text_lower

def contains_negation(text: str, keyword: str) -> bool:
    """Check if keyword appears in a negated context."""
    # Simple window-based negation detection
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    idx = text_lower.find(keyword_lower)
    if idx == -1:
        return False
    # Check 50 chars before keyword
    window = text_lower[max(0, idx-50):idx]
    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, window):
            return True
    return False

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two lat/lng points in km."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

def fuzzy_match(query: str, choices: List[str], threshold: int = 80) -> List[Tuple[str, int]]:
    """Fuzzy match query against choices."""
    return process.extract(query, choices, scorer=fuzz.WRatio, score_cutoff=threshold, limit=5)