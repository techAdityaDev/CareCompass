# CareCompass — AI Care Navigation & Caregiver Matching

**HACK IIITD · CAI, IIIT-Delhi** | Track: AI for Healthcare Access

> A production-ready, API-first, Dockerised proof-of-concept for intelligent care triage and caregiver matching. Built for elderly and low-literacy users with multilingual (English/Hindi/Hinglish) voice support.

---

## 🎯 Problem Statement

Patients often cannot articulate what care they need. CareCompass takes a free-text/voice request (e.g., *"papa ko do din se bukhar hai aur khansi bhi"*) and within seconds decides:
1. **WHAT CARE FITS** — Paramedic visit, Nurse, GP Teleconsult, Specialist, or Emergency
2. **HOW URGENT** — Routine, Same-day, or Immediate
3. **WHO SHOULD GO** — Best caregiver by skill, distance, availability, language

**Safety First:** Any red-flag symptom → immediate emergency escalation (112), no matching.

---

## 🏗️ Architecture

User Input (Text/Voice/Hinglish) │ ▼ ┌─────────────────────────────────────┐ │ Module 0: SAFETY GATE │ Deterministic + ML red-flag detection │ (Runs FIRST on every turn) │ ESCALATE IF EITHER FIRES └──────────────────┬──────────────────┘ │ No red flags ▼ ┌─────────────────────────────────────┐ │ Module 1: SMART INTAKE │ Extract structured symptoms │ │ Ask ≤3 targeted follow-ups └──────────────────┬──────────────────┘ │ Enough info ▼ ┌─────────────────────────────────────┐ │ Module 2: TRIAGE │ Care type + Urgency + Reasoning │ (Rules + LightGBM classifier) │ Asymmetric costs → prefer urgent └──────────────────┬──────────────────┘ │ If not emergency ▼ ┌─────────────────────────────────────┐ │ Module 3: CAREGIVER MATCHING │ Rank by language, proximity, skill, │ (Weighted scoring + explainability) │ rating, availability └─────────────────────────────────────┘


---

## 📊 Scoring Rubric Alignment

| Criterion | Weight | Implementation |
|-----------|--------|----------------|
| **Routing Accuracy** | 30% | Macro-F1 optimized LightGBM + char n-grams for Hinglish robustness |
| **Safety** | 20% | **100% recall** on training emergencies; deterministic lexicon + ML union |
| **Matching Quality** | 20% | NDCG@3 optimized weights; explainable reasons per caregiver |
| **UX & Demo** | 20% | Voice-first, multilingual, elderly-friendly UI, <2s latency |
| **Explainability** | 10% | Plain-language reasoning for every decision |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) TinyFish API key for doctor consultation demo

### 1. Clone & Configure
```bash
git clone <your-repo>
cd carecompass
cp .env.example .env
# Edit .env and add your TINYFISH_API_KEY