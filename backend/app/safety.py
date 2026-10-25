# backend/app/safety.py
"""
Module 0: Safety Gate - Deterministic high-recall red-flag detector.
Runs FIRST on every turn. ESCALATE IF EITHER RULE-BASED OR ML FIRES.
"""
import re
from typing import List, Set, Tuple
import pandas as pd
from app.utils import normalize_text, transliterate_if_needed, expand_hinglish, contains_negation
from app.schemas import RedFlag
from app.data_loader import CARE_TAXONOMY

# --- Red-flag keyword lexicon (multilingual) ---
RED_FLAG_LEXICON = {
    RedFlag.CHEST_PAIN: [
        # English
        "chest pain", "chest tightness", "chest pressure", "heart pain", "cardiac pain",
        "angina", "heart attack", "myocardial infarction",
        # Hinglish/Roman
        "seene mein dard", "chini mein dard", "chati mein dard", "dil mein dard",
        "seene ka dard", "chest ka dard", "heart ka dard",
        # Devanagari (transliterated)
        "seene me dard", "chati me dard", "dil me dard",
    ],
    RedFlag.BREATHLESSNESS: [
        # English
        "breathlessness", "shortness of breath", "difficulty breathing", "can't breathe",
        "cannot breathe", "gasping", "suffocating", "dyspnea", "respiratory distress",
        # Hinglish
        "saans phoolna", "saans phool rahi", "saans nahi aa rahi", "saans lene mein dikkat",
        "dam ghutna", "dam ghut raha", "saans rukna", "saans takleef",
        "saans uthna", "saans phulna", "saans lena mushkil",
        # Devanagari
        "saans phulna", "saans nahi aa rahi", "dam ghutna",
    ],
    RedFlag.UNCONSCIOUSNESS: [
        # English
        "unconscious", "unresponsive", "not responding", "collapsed", "fainted",
        "passed out", "blacked out", "coma", "won't wake up",
        # Hinglish
        "behosh", "behoshi", "behosh ho gaya", "behosh ho gayi",
        "gir gaye", "gir gayi", "gir gaya", "response nahi de rahe",
        "jawab nahi de rahe", "uth nahi rahe", "uth nahi rahi",
        "sudden collapse", "suddenly fell",
        # Devanagari
        "behosh", "gir gaye", "jawab nahi de rahe",
    ],
    RedFlag.SEVERE_BLEEDING: [
        # English
        "severe bleeding", "heavy bleeding", "bleeding won't stop", "bleeding not stopping",
        "profuse bleeding", "massive bleeding", "hemorrhage", "blood loss",
        # Hinglish
        "khoon nahi ruk raha", "khoon ruk nahi rahi", "bahut khoon", "jyada khoon",
        "bleeding ruk nahi rahi", "khoon bahna", "rakht srav",
        # Devanagari
        "khoon nahi ruk raha", "bahut khoon",
    ],
    RedFlag.STROKE_SYMPTOMS: [
        # English
        "stroke", "facial droop", "face drooping", "arm weakness", "speech difficulty",
        "slurred speech", "can't speak", "cannot speak", "one side weakness",
        "facial paralysis", "bell's palsy",
        # Hinglish
        "munh tedha", "muh tedha", "chehra tedha", "bol nahi pa rahe",
        "awaz nahi nikal rahi", "haath kaam nahi kar raha", "pair kaam nahi kar raha",
        "ek taraf kaam nahi kar raha", "lakwa", "paralysis",
        # Devanagari
        "munh tedha", "bol nahi pa rahe", "haath kaam nahi kar raha",
    ],
    RedFlag.SEIZURE: [
        # English
        "seizure", "convulsion", "had a fit", "having a fit", "fits aaye", "shaking uncontrollably",
        "jerking", "epilepsy", "tonic clonic",
        # Hinglish
        "daura", "mirgi", "daura pada", "jhatke", "akadna",
        "sharir akadna",
        # Devanagari
        "daura", "mirgi", "jhatke",
    ],
    RedFlag.HIGH_FEVER_INFANT: [
        # English
        "high fever infant", "baby high fever", "infant fever", "newborn fever",
        "child high fever", "baby temperature", "infant temperature",
        # Hinglish
        "bachche ka tez bukhar", "baby ka bukhar", "chhote bachche ka bukhar",
        "navjaat shishu ka bukhar", "bachche ko tez bukhar",
        # Devanagari
        "bachche ka tez bukhar", "baby ka bukhar",
    ],
     RedFlag.SUICIDAL_IDEATION: [
        "suicidal", "suicide", "kill myself", "want to die", "end my life",
        "khudkushi", "khud khushi", "marna chahte hain", "marna chahta hoon",
        "jeena nahi chahte", "aatmahatya", "self harm",
    ],
    RedFlag.SEVERE_DEHYDRATION: [
        "severe dehydration", "no urine", "not urinating",
        "sunken eyes", "can't keep fluids", "cannot keep fluids",
        "peshab nahi aa raha",
    ],
}

# Compile regex patterns for speed
_COMPILED_PATTERNS = {}
for flag, terms in RED_FLAG_LEXICON.items():
    # Word-boundary aware patterns for each term
    patterns = []
    for term in terms:
        escaped = re.escape(term)
        patterns.append(rf"(?<!\w){escaped}(?!\w)")
    _COMPILED_PATTERNS[flag] = [re.compile(p, re.IGNORECASE) for p in patterns]

def detect_red_flags_rule_based(text: str) -> List[RedFlag]:
    """
    Deterministic high-recall red-flag detection.
    Returns list of triggered RedFlag enums.
    """
    if not text:
        return []
    
    # Normalize: expand Hinglish, transliterate Devanagari
    normalized = expand_hinglish(transliterate_if_needed(normalize_text(text)))
    
    triggered = []
    for flag, patterns in _COMPILED_PATTERNS.items():
        for pattern in patterns:
            # Check every occurrence: one negated mention must not hide a real one
            for match in pattern.finditer(normalized):
                if not contains_negation(normalized, match.group(), match.start()):
                    triggered.append(flag)
                    break
            if flag in triggered:
                break  # One match per flag is enough
    return triggered

# --- ML Second Opinion (LightGBM on top of TF-IDF) ---
class MLRedFlagDetector:
    """Lightweight ML detector for edge cases. Trained on synthetic data."""
    
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self._load_or_train()
    
    def _load_or_train(self):
        from pathlib import Path
        import joblib
        from app.config import get_settings
        settings = get_settings()
        model_path = settings.MODEL_DIR / "redflag_ml.joblib"
        vec_path = settings.MODEL_DIR / "redflag_tfidf.joblib"
        
        if model_path.exists() and vec_path.exists():
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(vec_path)
        else:
            self._train()
            settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, model_path)
            joblib.dump(self.vectorizer, vec_path)
    
    def _train(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from lightgbm import LGBMClassifier
        from sklearn.multioutput import MultiOutputClassifier
        from app.data_loader import load_training_data
        from app.utils import expand_hinglish, transliterate_if_needed, normalize_text
        
        df = load_training_data()
        # Prepare labels: multi-label for each red flag
        texts = df["user_input"].apply(
            lambda x: expand_hinglish(transliterate_if_needed(normalize_text(str(x))))
        ).tolist()
        
        # Multi-label targets
        flag_list = [rf.value for rf in RedFlag]
        y = pd.DataFrame(0, index=df.index, columns=flag_list)
        for idx, row in df.iterrows():
            if pd.notna(row["red_flags"]):
                for flag in str(row["red_flags"]).split(";"):
                    flag = flag.strip()
                    if flag in flag_list:
                        y.at[idx, flag] = 1
        
        # TF-IDF char n-grams (robust to spelling variations)
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), max_features=5000,
            sublinear_tf=True, min_df=2
        )
        X = self.vectorizer.fit_transform(texts)
        
        # LightGBM with class_weight for recall
        base_clf = LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            class_weight="balanced", verbosity=-1, random_state=42,
            objective="binary", metric="auc"
        )
        self.model = MultiOutputClassifier(base_clf, n_jobs=-1)
        self.model.fit(X, y)
    
    def predict(self, text: str) -> List[RedFlag]:
        from app.utils import expand_hinglish, transliterate_if_needed, normalize_text
        normalized = expand_hinglish(transliterate_if_needed(normalize_text(text)))
        X = self.vectorizer.transform([normalized])
        preds = self.model.predict(X)[0]
        flag_list = [rf.value for rf in RedFlag]
        return [RedFlag(flag_list[i]) for i, p in enumerate(preds) if p == 1]

# Singleton
_ml_detector = None
def get_ml_detector() -> MLRedFlagDetector:
    global _ml_detector
    if _ml_detector is None:
        _ml_detector = MLRedFlagDetector()
    return _ml_detector

# --- Main Safety Gate ---
def safety_gate(text: str, conversation_history: list = None) -> Tuple[List[RedFlag], bool, str]:
    """
    Returns: (red_flags, is_emergency, reasoning)
    ESCALATE IF EITHER RULE-BASED OR ML FIRES.
    """
    # Combine current input with recent history for context
    full_text = text
    if conversation_history:
        user_msgs = [m for m in conversation_history if getattr(m.role, "value", m.role) == "user"]
        recent = " ".join([msg.content for msg in user_msgs[-3:]])
        full_text = recent + " " + text
    
    # Rule-based (high recall)
    rule_flags = detect_red_flags_rule_based(full_text)
    
    # ML second opinion
    ml_flags = get_ml_detector().predict(full_text)
    
    # Union: escalate if EITHER fires
    all_flags = list(set(rule_flags) | set(ml_flags))
    
    is_emergency = len(all_flags) > 0
    reasoning = ""
    if is_emergency:
        flag_names = [f.value.replace("_", " ") for f in all_flags]
        reasoning = f"Red-flag symptoms detected ({', '.join(flag_names)}); routed to emergency services."
    
    return all_flags, is_emergency, reasoning

# --- Evaluation helper ---
def evaluate_safety_recall() -> dict:
    """Measure recall on training set red-flag cases."""
    from app.data_loader import load_training_data
    df = load_training_data()
    emergency_cases = df[df["care_type"] == "emergency_112"]
    
    total = len(emergency_cases)
    caught = 0
    false_alarms = 0
    
    for _, row in df.iterrows():
        flags, is_emergency, _ = safety_gate(row["user_input"])
        true_emergency = row["care_type"] == "emergency_112"
        
        if true_emergency and is_emergency:
            caught += 1
        elif not true_emergency and is_emergency:
            false_alarms += 1
    
    return {
        "recall": caught / total if total > 0 else 1.0,
        "false_alarm_rate": false_alarms / (len(df) - total) if len(df) > total else 0.0,
        "total_emergencies": total,
        "caught": caught,
        "false_alarms": false_alarms
    }