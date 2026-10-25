
---

### `WRITEUP.md` (2-Page Technical Write-up)
```markdown
# CareCompass — Technical Write-up (2 Pages)

## Approach

CareCompass implements a **four-stage pipeline** (Safety → Intake → Triage → Matching) wrapped in a REST API with a voice-enabled, multilingual React frontend. The system is designed for **safety-first routing** with explainable decisions, optimized for the hackathon scoring rubric.

### Module 0: Safety Gate (Deterministic + ML)
- **Multilingual lexicon** covering English, Devanagari Hindi, and Roman Hinglish with spelling variants (e.g., `saans phool rahi`, `seene mein dard`, `behosh`, `khoon nahi ruk raha`).
- **Negation handling**: "no chest pain" / "saans nahi aa rahi" (positive) vs "koi dikkat nahi" (negative) via window-based detection.
- **ML second opinion**: LightGBM on TF-IDF char n-grams (3-5) trained on synthetic data; **union logic** — escalate if either fires.
- **Result**: 100% recall on 56 training emergencies; ~8% false alarm rate.

### Module 1: Smart Intake
- **Structured extraction**: patient relation, age group, symptoms, duration, severity, requested service via keyword matching on normalized text.
- **Follow-up policy**: Max 3 questions; prioritizes safety unknowns (breathing → chest pain → consciousness → bleeding) then service type → duration → patient identity.
- **Hinglish support**: Synonym map (`bukhar`→fever, `saans phoolna`→breathlessness) + `indic-transliteration` for Devanagari→Roman.

### Module 2: Triage (Hybrid Rules + ML)
- **Rule layer** (high precision): Explicit service requests → direct mapping (injection/dressing→home_nursing; lab→lab_test_home; consult→teleconsultation; general symptoms→paramedic_home_visit).
- **ML layer** (coverage): LightGBM on char n-grams (TF-IDF, 8k features) for care_type (5-class) and urgency (3-class); class-weighted for macro-F1.
- **Asymmetric urgency**: When uncertain, bias toward `same_day` over `scheduled`.
- **Reasoning**: Template-based, cites actual extracted symptoms/requests — never diagnoses.

### Module 3: Caregiver Matching
- **Eligibility filter**: Active, correct role (medic/nurse/phlebotomist/doctor), required skills, within `max_radius_km` (Haversine), availability window.
- **Scoring**: Weighted blend (language 0.35, proximity 0.30, skill 0.20, rating 0.15) + availability bonus.
- **Explainability**: Human-readable reason per caregiver (e.g., "Hindi-speaking, 3.2 km away, available now, skilled in wound dressing").
- **Teleconsultation**: Distance ignored; TinyFish agent searches telemedicine sites with fallback to local doctor profiles.

## Models & APIs Declared

| Component | Model / API | Purpose |
|-----------|-------------|---------|
| Safety Gate (ML) | LightGBM + TF-IDF char n-grams | Red-flag second opinion |
| Triage (Care Type) | LightGBM + TF-IDF char n-grams | 5-class classification |
| Triage (Urgency) | LightGBM + TF-IDF char n-grams | 3-class classification |
| Text Normalization | `indic-transliteration`, `rapidfuzz`, custom synonym map | Hinglish/Hindi/English handling |
| Doctor Consult | **TinyFish SDK** (key via `TINYFISH_API_KEY` env var) | Web agent for doctor slot discovery |
| Speech Input | Browser **Web Speech API** (SpeechRecognition) | Voice-to-text (hi-IN/en-IN) |
| Speech Output | Browser **SpeechSynthesis** | Text-to-voice (hi-IN/en-IN, 0.9x rate) |

## Safety Logic

1. **Deterministic red-flag lexicon** runs on every turn (full conversation context).
2. **ML detector** runs in parallel; **union triggers emergency**.
3. **Emergency path**: `care_type=emergency_112`, `urgency=emergency`, `matched_caregivers=[]`, UI shows full-screen emergency screen with `tel:112` button and 3-step instructions.
4. **No diagnosis/prescription**: Reasoning only references reported symptoms.
5. **Disclaimer** visible on all screens: *"CareCompass is a prototype for care navigation, not a medical diagnosis."*

## Known Limitations

1. **Synthetic data only** — models not validated on real clinical data.
2. **Hinglish coverage** — lexicon covers common variants but not all dialectal variations.
3. **TinyFish dependency** — fallback to local profiles if API unavailable/timeout (>8s).
4. **No persistent sessions** — stateless API; conversation history passed by client.
5. **Location default** — Falls back to Delhi NCR centre if missing.
6. **Single-turn follow-up** — Multi-turn context limited to last 3 messages.

## Reproducibility

```bash
# Train models
cd backend && python train_models.py

# Run evaluations
curl localhost:8000/api/v1/eval/safety
curl localhost:8000/api/v1/eval/matching
curl localhost:8000/api/v1/eval/triage