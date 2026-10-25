# backend/app/tinyfish.py
"""
TinyFish wrapper for doctor consultation discovery.
Fallback to local doctor profiles if TinyFish unavailable.
"""
import os
import asyncio
import logging
import pandas as pd
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from app.schemas import DoctorSlot, TeleconsultResponse
from app.data_loader import load_caregivers
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

@dataclass
class TinyFishResult:
    doctors: List[DoctorSlot]
    success: bool
    error: Optional[str] = None

class TinyFishClient:
    """Wrapper around TinyFish SDK for doctor slot discovery."""
    
    def __init__(self):
        self.api_key = settings.TINYFISH_API_KEY or os.getenv("TINYFISH_API_KEY", "")
        self.client = None
        self.async_client = None
        self._init_clients()
    
    def _init_clients(self):
        if not self.api_key:
            logger.warning("TINYFISH_API_KEY not set; will use fallback only")
            return
        try:
            from tinyfish import TinyFish, AsyncTinyFish
            self.client = TinyFish(api_key=self.api_key)
            self.async_client = AsyncTinyFish(api_key=self.api_key)
        except ImportError:
            logger.warning("tinyfish package not installed; using fallback")
    
    async def find_doctors(self, specialty: Optional[str] = None, language: str = "en") -> TinyFishResult:
        """Use TinyFish agent to search for available online doctor consultations."""
        if not self.async_client:
            return TinyFishResult([], False, "TinyFish not configured")
        
        try:
            # Build search query
            query_parts = ["online doctor consultation", "video call", "book appointment"]
            if specialty:
                query_parts.append(specialty)
            if language == "hi":
                query_parts.append("Hindi")
            query = " ".join(query_parts)
            
            # Search for relevant pages
            search_results = await self.async_client.search.query(query=query)
            
            # Target known telemedicine platforms
            target_domains = [
                "practo.com", "1mg.com", "pharmeasy.in", "apollotelehealth.com",
                "tatahealth.com", "mfine.co", "docsapp.in", "lybrate.com"
            ]
            
            urls = []
            for result in search_results.results[:10]:
                url = result.url
                if any(domain in url for domain in target_domains):
                    urls.append(url)
            
            if not urls:
                return TinyFishResult([], False, "No telemedicine pages found")
            
            # Run agents in parallel
            goal = (
                f"Find available {specialty or 'general'} doctor consultation slots for "
                f"{'Hindi' if language == 'hi' else 'English'} speaking patients. "
                "Return doctor name, language, rating, next available slot, and booking link."
            )
            
            schema = {
                "type": "object",
                "properties": {
                    "doctors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "language": {"type": "string"},
                                "rating": {"type": "number"},
                                "next_slot": {"type": "string"},
                                "booking_url": {"type": "string"},
                            }
                        }
                    }
                }
            }
            
            runs = await asyncio.gather(*[
                self.async_client.agent.run(url=url, goal=goal, output_schema=schema)
                for url in urls[:5]
            ], return_exceptions=True)
            
            doctors = []
            for run in runs:
                if isinstance(run, Exception) or run.status != "COMPLETED":
                    continue
                if run.result and "doctors" in run.result:
                    for d in run.result["doctors"]:
                        doctors.append(DoctorSlot(
                            doctor_id=f"tf_{hash(d.get('booking_url', '')) % 10000}",
                            name=d.get("name", "Doctor"),
                            language=d.get("language", "English"),
                            rating=float(d.get("rating", 4.0)),
                            next_slot=d.get("next_slot", ""),
                            profile_url=d.get("booking_url")
                        ))
            
            return TinyFishResult(doctors[:5], True)
        
        except Exception as e:
            logger.error(f"TinyFish error: {e}")
            return TinyFishResult([], False, str(e))

def get_fallback_doctors(language: str = "en", specialty: Optional[str] = None) -> List[DoctorSlot]:
    """Fallback: use local caregiver profiles with role=doctor."""
    caregivers = load_caregivers()
    doctors = caregivers[
        (caregivers["role"] == "doctor") & 
        (caregivers["active"] == True)
    ].copy()
    
    # Language filter
    lang_lower = language.lower()
    if lang_lower in ["hi", "hinglish"]:
        doctors = doctors[doctors["languages"].apply(
            lambda langs: any(l.lower() in ["hindi", "hinglish"] for l in langs)
        )]
    elif lang_lower == "en":
        doctors = doctors[doctors["languages"].apply(
            lambda langs: "english" in [l.lower() for l in langs]
        )]
    
    # Sort by rating
    doctors = doctors.sort_values("rating", ascending=False).head(5)
    
    slots = []
    for _, doc in doctors.iterrows():
        # Generate a plausible next slot
        free_from = doc["free_from"]
        if pd.isna(free_from):
            next_slot = "Contact for availability"
        else:
            next_slot = f"Today {free_from.strftime('%H:%M')} IST"
        
        slots.append(DoctorSlot(
            doctor_id=doc["caregiver_id"],
            name=doc["name"],
            language=", ".join(doc["languages"][:2]),
            rating=doc["rating"],
            next_slot=next_slot,
            profile_url=None
        ))
    
    return slots

# Singleton
_tinyfish_client = None
def get_tinyfish_client() -> TinyFishClient:
    global _tinyfish_client
    if _tinyfish_client is None:
        _tinyfish_client = TinyFishClient()
    return _tinyfish_client

async def find_doctor_consultation(
    language: str = "en",
    specialty: Optional[str] = None,
    preferred_time: Optional[str] = None
) -> TeleconsultResponse:
    """Main entry point for doctor consultation discovery."""
    client = get_tinyfish_client()
    
    # Try TinyFish first
    result = await client.find_doctors(specialty, language)
    
    if result.success and result.doctors:
        return TeleconsultResponse(
            doctors=result.doctors,
            fallback_used=False,
            message=f"Found {len(result.doctors)} available doctors via TinyFish"
        )
    
    # Fallback to local profiles
    logger.info(f"TinyFish fallback: {result.error}")
    fallback_doctors = get_fallback_doctors(language, specialty)
    
    return TeleconsultResponse(
        doctors=fallback_doctors,
        fallback_used=True,
        message=f"Using local doctor profiles (TinyFish: {result.error or 'unavailable'})"
    )