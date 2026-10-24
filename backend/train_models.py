#!/usr/bin/env python
"""
One-shot training script for all ML models.
Run once after data is in place: python train_models.py
"""
import sys
sys.path.insert(0, '.')

from app.safety import get_ml_detector, evaluate_safety_recall
from app.triage import get_triage_classifier
from app.matching import evaluate_matching
from app.config import get_settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    settings = get_settings()
    settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("Training Safety Gate (Red-Flag Detector)")
    logger.info("=" * 60)
    _ = get_ml_detector()  # Triggers training
    safety_metrics = evaluate_safety_recall()
    logger.info(f"Safety Recall: {safety_metrics['recall']:.2%}")
    logger.info(f"False Alarm Rate: {safety_metrics['false_alarm_rate']:.2%}")
    
    if safety_metrics['recall'] < 1.0:
        logger.warning("⚠️ Safety recall < 100% on training set! Review red-flag lexicon.")
    else:
        logger.info("✅ Safety recall = 100% on training set")
    
    logger.info("\n" + "=" * 60)
    logger.info("Training Triage Classifier (Care Type + Urgency)")
    logger.info("=" * 60)
    _ = get_triage_classifier()  # Triggers training
    logger.info("✅ Triage classifier trained")
    
    logger.info("\n" + "=" * 60)
    logger.info("Evaluating Caregiver Matcher")
    logger.info("=" * 60)
    match_metrics = evaluate_matching()
    logger.info(f"Mean NDCG@3: {match_metrics['mean_ndcg_at_3']:.3f}")
    logger.info(f"Top-1 Agreement: {match_metrics['top1_agreement_rate']:.2%}")
    
    logger.info("\n" + "=" * 60)
    logger.info("All models trained and saved to %s", settings.MODEL_DIR)
    logger.info("=" * 60)

if __name__ == '__main__':
    main()