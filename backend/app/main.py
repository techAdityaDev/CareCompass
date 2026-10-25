# backend/app/main.py
"""
CareCompass FastAPI Application - Main Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import logging
from pathlib import Path

from app.config import get_settings
from app.schemas import (
    CareType, Urgency, TriageRequest, TriageResponse, HealthResponse,
    BookingRequest, BookingResponse,
    TeleconsultRequest, TeleconsultResponse,
    BatchPredictRequest, BatchPredictResponse
)
from app.safety import safety_gate, evaluate_safety_recall
from app.intake import extract_structured, select_follow_up, should_ask_follow_up
from app.triage import triage
from app.matching import match_caregivers, evaluate_matching
from app.tinyfish import find_doctor_consultation
from app.data_loader import load_training_data, load_caregivers

settings = get_settings()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for models/data
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CareCompass API...")
    # Pre-load data and models
    load_training_data()
    load_caregivers()
    # Warm up models
    from app.safety import get_ml_detector
    from app.triage import get_triage_classifier
    get_ml_detector()
    get_triage_classifier()
    app_state["models_loaded"] = True
    app_state["data_loaded"] = True
    logger.info("CareCompass API ready")
    yield
    # Shutdown
    logger.info("Shutting down CareCompass API...")

app = FastAPI(
    title="CareCompass API",
    description="AI-powered care navigation and caregiver matching",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files in production
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

# --- Health Check ---
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        models_loaded=app_state.get("models_loaded", False),
        data_loaded=app_state.get("data_loaded", False)
    )

# --- Main Triage Endpoint ---
@app.post("/api/v1/triage", response_model=TriageResponse)
async def triage_endpoint(request: TriageRequest):
    try:
        # Default location if not provided
        location = request.location
        if not location:
            location = type('obj', (object,), {
                'lat': settings.DEFAULT_LAT,
                'lng': settings.DEFAULT_LNG
            })()
        
        # Module 0: Safety Gate (runs first, on full conversation)
        # Only the USER's words go to the safety gate. The assistant's own follow-up
        # questions ("any chest pain?") must never trigger a red flag.
        user_history = [m for m in (request.conversation_history or []) if m.role.value == "user"]
        conversation_text = " ".join([m.content for m in user_history] + [request.user_input])
        
        red_flags, is_emergency, safety_reasoning = safety_gate(conversation_text, user_history)
        
        if is_emergency:
            return TriageResponse(
                follow_up_question=None,
                care_type=CareType.EMERGENCY_112,
                urgency=Urgency.EMERGENCY,
                red_flags=red_flags,
                reasoning=safety_reasoning,
                matched_caregivers=[]
            )
        
        # Module 1: Smart Intake
        structured = extract_structured(request.user_input, request.conversation_history)
        
        # Count previous follow-ups in this conversation
        follow_up_count = sum(
            1 for msg in request.conversation_history 
            if msg.role.value == "assistant" and "?" in msg.content
        )
        
        # Decide if we need follow-up
        if should_ask_follow_up(structured, follow_up_count):
            follow_up = select_follow_up(structured, request.conversation_history)
            if follow_up:
                question = follow_up.get(request.language, follow_up["en"])
                return TriageResponse(
                    follow_up_question=question,
                    care_type=None,
                    urgency=None,
                    red_flags=[],
                    reasoning="Need more information to determine appropriate care.",
                    matched_caregivers=[]
                )
        
        # Module 2: Triage
        triage_result = triage(structured, red_flags)
        
        # Module 3: Caregiver Matching
        matched = match_caregivers(
            triage_result.care_type,
            location.lat,
            location.lng,
            structured.language,
            top_k=3
        )
        
        return TriageResponse(
            follow_up_question=None,
            care_type=triage_result.care_type,
            urgency=triage_result.urgency,
            red_flags=red_flags,
            reasoning=triage_result.reasoning,
            matched_caregivers=matched
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        logger.exception("Triage error")
        raise HTTPException(status_code=500, detail="Internal server error")

# --- Batch Predict ---
@app.post("/api/v1/batch_predict", response_model=BatchPredictResponse)
async def batch_predict(request: BatchPredictRequest):
    """Process CSV file and return predictions."""
    import io
    import base64
    import pandas as pd
    
    try:
        # Decode CSV
        csv_content = request.csv_content
        if csv_content.startswith("data:"):
            # Handle base64 data URL
            csv_content = base64.b64decode(csv_content.split(",")[1]).decode("utf-8")
        
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Required columns
        required = ["id", "user_input", "lat", "lng"]
        for col in required:
            if col not in df.columns:
                raise HTTPException(400, f"Missing required column: {col}")
        
        predictions = []
        for _, row in df.iterrows():
            req = TriageRequest(
                user_input=row["user_input"],
                location={"lat": row["lat"], "lng": row["lng"]},
                conversation_history=[]
            )
            resp = await triage_endpoint(req)
            
            predictions.append({
                "id": row["id"],
                "care_type": resp.care_type.value if resp.care_type else "",
                "urgency": resp.urgency.value if resp.urgency else "",
                "red_flags": ";".join([rf.value for rf in resp.red_flags]),
                "follow_up_question": resp.follow_up_question or "",
            })
        
        pred_df = pd.DataFrame(predictions)
        output_csv = pred_df.to_csv(index=False)
        
        return BatchPredictResponse(
            predictions_csv=output_csv,
            processed_count=len(predictions)
        )
    
    except Exception as e:
        logger.exception("Batch predict error")
        raise HTTPException(status_code=500, detail=str(e))

# --- Booking ---
@app.post("/api/v1/book", response_model=BookingResponse)
async def book_caregiver(request: BookingRequest):
    """Simulate booking a caregiver."""
    caregivers = load_caregivers()
    cg = caregivers[caregivers["caregiver_id"] == request.caregiver_id]
    
    if cg.empty:
        raise HTTPException(404, "Caregiver not found")
    
    cg = cg.iloc[0]
    
    # Simulate booking
    import uuid
    booking_id = f"BK_{uuid.uuid4().hex[:8].upper()}"
    
    return BookingResponse(
        booking_id=booking_id,
        status="confirmed",
        message=f"Booking confirmed with {cg['name']}",
        caregiver_name=cg["name"],
        estimated_arrival="30-45 minutes"  # Mock
    )

# --- Teleconsultation (TinyFish) ---
@app.post("/api/v1/teleconsult", response_model=TeleconsultResponse)
async def teleconsult(request: TeleconsultRequest):
    """Find available doctor for video consultation."""
    try:
        result = await find_doctor_consultation(
            language=request.language,
            specialty=request.specialty,
            preferred_time=request.preferred_time
        )
        return result
    except Exception as e:
        logger.exception("Teleconsult error")
        raise HTTPException(status_code=500, detail=str(e))

# --- Evaluation Endpoints (for debugging) ---
@app.get("/api/v1/eval/safety")
async def eval_safety():
    return evaluate_safety_recall()

@app.get("/api/v1/eval/matching")
async def eval_matching():
    return evaluate_matching()

@app.get("/api/v1/eval/triage")
async def eval_triage():
    """Run full triage evaluation on holdout set."""
    from app.data_loader import load_training_data
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, confusion_matrix
    import pandas as pd
    import numpy as np
    
    df = load_training_data()
    df_labeled = df[df["care_type"].notna()].copy()
    
    # Split
    train_df, test_df = train_test_split(df_labeled, test_size=0.2, stratify=df_labeled["care_type"], random_state=42)
    
    y_true_care = []
    y_pred_care = []
    y_true_urg = []
    y_pred_urg = []
    
    for _, row in test_df.iterrows():
        req = TriageRequest(
            user_input=row["user_input"],
            location={"lat": row["lat"], "lng": row["lng"]},
            conversation_history=[]
        )
        resp = await triage_endpoint(req)
        
        y_true_care.append(row["care_type"])
        y_pred_care.append(resp.care_type.value if resp.care_type else "null")
        y_true_urg.append(row["urgency"])
        y_pred_urg.append(resp.urgency.value if resp.urgency else "null")
    
    return {
        "care_type_report": classification_report(y_true_care, y_pred_care, output_dict=True, zero_division=0),
        "urgency_report": classification_report(y_true_urg, y_pred_urg, output_dict=True, zero_division=0),
        "care_type_confusion": confusion_matrix(y_true_care, y_pred_care).tolist(),
        "urgency_confusion": confusion_matrix(y_true_urg, y_pred_urg).tolist(),
        "test_size": len(test_df)
    }

if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)