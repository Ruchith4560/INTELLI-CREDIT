from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app import models
from app.utils.auth import get_current_user

router = APIRouter()


class FeedbackCreate(BaseModel):
    session_id:           str
    agreed_with_decision: bool
    actual_decision:      Optional[str] = None
    comments:             Optional[str] = ""


@router.post("/submit")
def submit_feedback(
    feedback:     FeedbackCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    fb = models.OfficerFeedback(
        session_id           = feedback.session_id,
        user_id              = current_user.id,
        agreed_with_decision = feedback.agreed_with_decision,
        actual_decision      = feedback.actual_decision,
        comments             = feedback.comments,
    )
    db.add(fb)
    db.commit()
    return {"message": "Feedback submitted. This will improve the model over time."}


@router.get("/stats")
def feedback_stats(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    total  = db.query(models.OfficerFeedback).count()
    agreed = db.query(models.OfficerFeedback).filter(
        models.OfficerFeedback.agreed_with_decision == True
    ).count()
    return {
        "total_feedback": total,
        "agreed":         agreed,
        "disagreed":      total - agreed,
        "accuracy_rate":  round(agreed / total * 100, 1) if total > 0 else 0,
    }
