
---

### `DEMO_SCRIPT.md` (3-Minute Video Script)
```markdown
# CareCompass — 3-Minute Demo Script

## Scenario A: Hinglish Fever Case → Paramedic Visit (60s)
**Goal**: Show multilingual voice input, one follow-up, booking.

1. **Open app** → Language: **Hinglish** (show toggle)
2. **Tap 🎤** → Speak: *"papa ko do din se bukhar hai aur khansi bhi"*
3. **Confirm transcript** → "Sahi hai"
4. **System asks**: *"Kya unhe saans lene mein takleef hai?"* (Hinglish, big buttons)
5. **Tap "Nahi"** → Instant result:
   - **Care**: Paramedic Home Visit
   - **Urgency**: Same Day
   - **Reasoning**: "Fever with cough for 2 days, no breathing difficulty reported"
   - **Top Caregiver**: "Ankit Gupta (CG_014) — Hindi-speaking, 3.2 km, available now, skilled in bp_sugar_check"
6. **Tap "Book Now"** → Confirmation screen with read-aloud.

## Scenario B: Chest Pain Emergency → 112 Screen (45s)
**Goal**: Demonstrate safety gate, immediate escalation, no caregiver matching.

1. **Language: Hindi** → Tap 🎤 → *"papa ko tej seene mein dard hai aur saans nahi aa rahi"*
2. **Confirm** → **Instant red screen** (no follow-up):
   - **🚨 EMERGENCY DETECTED**
   - Red flags: `chest_pain`, `breathlessness`
   - **Big red button**: "ABHI 112 CALL KAREIN" (tap → opens dialer)
   - 3 steps auto-read aloud in Hindi
   - **No caregiver list**, no booking option
3. **Tap "Start Over"** → Returns to welcome.

## Scenario C: Hindi Injection Request → Nurse Matching (45s)
**Goal**: Show service-specific routing, skill-based matching.

1. **Language: Hindi** → Quick tile: **"इंजेक्शन/ड्रेसिंग"**
2. **Auto-fills**: *"injection lagwana hai"* → No follow-up needed (high confidence)
3. **Result**: Home Nursing, Same Day
4. **Caregivers**: Top 3 ranked by skill match (injection_im), language, distance
   - Reasons show specific skill: *"skilled in injection IM"*
5. **Book** → Confirmation.

## Scenario D: Doctor Consult via TinyFish (30s)
**Goal**: Show teleconsultation flow with external API + fallback.

1. **Language: English** → Quick tile: **"Talk to Doctor"**
2. **Input**: *"want to talk to a doctor about my reports"*
3. **Result**: Teleconsultation, Same Day
4. **Tap "Talk to a Doctor"** → Loads doctor cards:
   - If TinyFish works: Real-time slots from Practo/1mg/etc.
   - **Fallback** (demo): Local doctors (Dr. Rekha Gupta 4.9⭐, available 14:00)
5. **Book video call** → External link / confirmation.

---

## Key Talking Points (Voiceover)

- **"Safety gate runs first on every turn — deterministic lexicon + ML, union logic ensures 100% recall on training emergencies."**
- **"Smart intake asks at most 3 questions, always targeting biggest safety unknown first."**
- **"Triage uses rules for clear cases, LightGBM for ambiguity; asymmetric costs bias toward urgency."**
- **"Matching explains every rank: language, distance, skill, availability — no black box."**
- **"Voice-first UI: Hinglish/Hindi/English, transcript confirmation, TTS at 0.9x for elderly users."**
- **"API-first: stateless /triage endpoint, batch_predict for hidden test, Dockerised for one-command deploy."**