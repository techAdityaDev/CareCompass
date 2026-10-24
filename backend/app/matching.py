# backend/app/matching.py
"""
Module 3: Caregiver Matching - Rank eligible caregivers with explainable scores.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import time, datetime
import pandas as pd
from app.utils import haversine_km
from app.schemas import CareType, MatchedCaregiver
from app.data_loader import load_caregivers, CARE_TAXONOMY
from app.config import get_settings

settings = get_settings()

CARE_TYPE_TO_ROLE = {
    CareType.PARAMEDIC_HOME_VISIT: "medic",
    CareType.HOME_NURSING: "medic",
    CareType.LAB_TEST_HOME: "phlebotomist",
    CareType.TELECONSULTATION: "doctor",
    CareType.EMERGENCY_112: None,
}

CARE_TYPE_TO_SKILLS = {
    CareType.PARAMEDIC_HOME_VISIT: ["vitals_monitoring", "assessment", "elderly_care", "sample_collection"],
    CareType.HOME_NURSING: ["injection_im", "injection_iv", "wound_dressing", "catheter_care", "post_surgical_care", "nebulization", "bp_sugar_check"],
    CareType.LAB_TEST_HOME: ["sample_collection", "home_phlebotomy"],
    CareType.TELECONSULTATION: ["teleconsultation", "prescription", "report_review"],
}

@dataclass
class ScoredCaregiver:
    caregiver_id: str
    name: str
    role: str
    score: float
    reason_parts: Dict[str, float]
    distance_km: float
    languages: List[str]
    skills: List[str]
    rating: float
    available: bool
    next_slot: str

def is_available_now(cg: pd.Series) -> Tuple[bool, str]:
    """Check if caregiver is available now. Returns (available, next_slot_str)."""
    now = datetime.now().time()
    free_from = cg["free_from"]
    free_until = cg["free_until"]
    
    if pd.isna(free_from) or pd.isna(free_until):
        return False, "Availability unknown"
    
    if free_from <= now <= free_until:
        return True, "Available now"
    elif now < free_from:
        return False, f"Free from {free_from.strftime('%H:%M')}"
    else:
        return False, "Shift ended"

def language_match_score(user_lang: str, cg_languages: List[str]) -> float:
    """Score language compatibility (0-1)."""
    user_lang = user_lang.lower()
    cg_langs = [l.lower() for l in cg_languages]
    
    # Direct match
    if user_lang in cg_langs:
        return 1.0
    
    # Hindi/Hinglish speakers match
    if user_lang in ["hindi", "hinglish"] and any(l in cg_langs for l in ["hindi", "hinglish"]):
        return 1.0
    if user_lang == "en" and "english" in cg_langs:
        return 1.0
    
    # Partial: any common language
    return 0.5

def proximity_score(distance_km: float, max_radius_km: float) -> float:
    """Proximity score: 1.0 at 0km, linear decay to 0 at max_radius."""
    if distance_km <= 0:
        return 1.0
    if distance_km >= max_radius_km:
        return 0.0
    return 1.0 - (distance_km / max_radius_km)

def skill_match_score(required_skills: List[str], cg_skills: List[str]) -> float:
    """Skill overlap score."""
    if not required_skills:
        return 1.0
    cg_set = set(cg_skills)
    matches = sum(1 for s in required_skills if s in cg_set)
    return matches / len(required_skills)

def normalize_rating(rating: float) -> float:
    """Normalize 1-5 rating to 0-1."""
    return max(0.0, min(1.0, (rating - 1.0) / 4.0))

def match_caregivers(
    care_type: CareType,
    user_lat: float,
    user_lng: float,
    user_language: str,
    top_k: int = 3
) -> List[MatchedCaregiver]:
    """Main matching function."""
    if care_type == CareType.EMERGENCY_112:
        return []
    
    caregivers = load_caregivers()
    required_role = CARE_TYPE_TO_ROLE.get(care_type)
    required_skills = CARE_TYPE_TO_SKILLS.get(care_type, [])
    
    # Filter eligible
    eligible = caregivers[
        (caregivers["active"] == True) &
        (caregivers["role"] == required_role)
    ].copy()
    
    if eligible.empty:
        return []
    
    # Distance filter
    eligible["distance_km"] = eligible.apply(
        lambda row: haversine_km(user_lat, user_lng, row["base_lat"], row["base_lng"]), axis=1
    )
    eligible = eligible[eligible["distance_km"] <= eligible["max_radius_km"]]
    
    if eligible.empty:
        return []
    
    # Availability
    eligible[["available", "next_slot"]] = eligible.apply(
        lambda row: pd.Series(is_available_now(row)), axis=1
    )
    # Prefer available, but don't exclude unavailable entirely (lower score)
    
    # Score each component
    weights = settings.MATCH_WEIGHTS
    
    scored = []
    for _, cg in eligible.iterrows():
        lang_score = language_match_score(user_language, cg["languages"])
        prox_score = proximity_score(cg["distance_km"], cg["max_radius_km"])
        skill_score = skill_match_score(required_skills, cg["skills"])
        rating_score = normalize_rating(cg["rating"])
        avail_bonus = 0.1 if cg["available"] else 0.0
        
        total_score = (
            weights["language"] * lang_score +
            weights["proximity"] * prox_score +
            weights["skill"] * skill_score +
            weights["rating"] * rating_score +
            avail_bonus
        )
        
        # Build human-readable reason
        reasons = []
        if lang_score >= 1.0:
            reasons.append(f"{cg['languages'][0]}-speaking")
        elif lang_score > 0:
            reasons.append("language match")
        
        reasons.append(f"{cg['distance_km']:.1f} km away")
        
        if cg["available"]:
            reasons.append("available now")
        else:
            reasons.append(cg["next_slot"])
        
        if skill_score > 0:
            matched = [s for s in required_skills if s in cg["skills"]]
            if matched:
                reasons.append(f"skilled in {matched[0].replace('_', ' ')}")
        
        reason_str = ", ".join(reasons)
        
        scored.append(ScoredCaregiver(
            caregiver_id=cg["caregiver_id"],
            name=cg["name"],
            role=cg["role"],
            score=round(total_score, 3),
            reason_parts={
                "language": lang_score,
                "proximity": prox_score,
                "skill": skill_score,
                "rating": rating_score,
                "availability": 1.0 if cg["available"] else 0.0
            },
            distance_km=round(cg["distance_km"], 1),
            languages=cg["languages"],
            skills=cg["skills"],
            rating=cg["rating"],
            available=cg["available"],
            next_slot=cg["next_slot"]
        ))
    
    # Sort by score descending
    scored.sort(key=lambda x: x.score, reverse=True)
    top = scored[:top_k]
    
    return [
        MatchedCaregiver(
            caregiver_id=cg.caregiver_id,
            score=cg.score,
            reason=cg.reason
        )
        for cg in top
    ]

def evaluate_matching() -> dict:
    """Evaluate NDCG@3 against reference matches in training data."""
    from app.data_loader import load_training_data
    from sklearn.metrics import ndcg_score
    import numpy as np
    
    df = load_training_data()
    df_labeled = df[df["matched_caregiver_ids"].notna()].copy()
    
    ndcg_scores = []
    top1_agreements = 0
    
    for _, row in df_labeled.iterrows():
        if row["care_type"] == "emergency_112":
            continue
        
        care_type = CareType(row["care_type"])
        ref_ids = [x.strip() for x in str(row["matched_caregiver_ids"]).split(";") if x.strip()]
        
        if not ref_ids:
            continue
        
        pred = match_caregivers(care_type, row["lat"], row["lng"], row["detected_language"].lower(), top_k=3)
        pred_ids = [c.caregiver_id for c in pred]
        
        # NDCG@3
        relevance = [1.0 if pid in ref_ids else 0.0 for pid in pred_ids]
        ideal = sorted(relevance, reverse=True)
        if sum(ideal) > 0:
            ndcg = ndcg_score([ideal], [relevance], k=3)
            ndcg_scores.append(ndcg)
        
        # Top-1 agreement
        if pred_ids and pred_ids[0] in ref_ids:
            top1_agreements += 1
    
    return {
        "mean_ndcg_at_3": float(np.mean(ndcg_scores)) if ndcg_scores else 0.0,
        "top1_agreement_rate": top1_agreements / len(df_labeled) if len(df_labeled) > 0 else 0.0,
        "evaluated_cases": len(df_labeled)
    }