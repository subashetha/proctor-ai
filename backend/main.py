"""
Online Exam Proctoring System - Backend
Author: AI Intern @ aumne.ai
"""

import time
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal, engine, Base
from models import Exam, Submission
from schemas import (
    ExamCreate, ExamResponse,
    SubmissionCreate, SubmissionResponse,
    SuspiciousFlag
)
from proctoring import analyze_submission, generate_audit_log

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Online Exam Proctoring System",
    description="AI-assisted cheating detection for online exams — built for aumne.ai internship challenge",
    version="1.0.0",
    contact={"name": "AI Intern", "email": "intern@aumne.ai"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Dependency ────────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Exam Endpoints ─────────────────────────────────────────────────────────────

@app.post("/exams/", response_model=ExamResponse, status_code=201, tags=["Exams"])
def create_exam(exam: ExamCreate, db: Session = Depends(get_db)):
    """Create a new exam with title and duration (minutes)."""
    if exam.duration <= 0:
        raise HTTPException(status_code=422, detail="Duration must be positive.")
    db_exam = Exam(title=exam.title.strip(), duration=exam.duration)
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam


@app.get("/exams/", response_model=List[ExamResponse], tags=["Exams"])
def list_exams(db: Session = Depends(get_db)):
    """List all available exams."""
    return db.query(Exam).all()


@app.get("/exams/{exam_id}", response_model=ExamResponse, tags=["Exams"])
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific exam by ID."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail=f"Exam {exam_id} not found.")
    return exam


# ── Submission Endpoints ───────────────────────────────────────────────────────

@app.post("/exams/{exam_id}/submit", response_model=SubmissionResponse, status_code=201, tags=["Submissions"])
def submit_exam(exam_id: int, submission: SubmissionCreate, db: Session = Depends(get_db)):
    """
    Submit answers for an exam.
    
    The proctoring engine will automatically flag suspicious activity:
    - Copy-paste detection (identical answers across questions)
    - Inactivity detection (time_taken_seconds > exam.duration * 60 * 0.9)
    - Abnormally fast submission (too quick)
    - Blank / empty answer submission
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail=f"Exam {exam_id} not found.")

    if not submission.user_name.strip():
        raise HTTPException(status_code=422, detail="user_name cannot be empty.")

    flags: List[SuspiciousFlag] = analyze_submission(submission, exam)
    is_suspicious = len(flags) > 0
    flag_reasons = [f.reason for f in flags]

    # Generate AI audit log for flagged submissions
    audit_log = None
    if is_suspicious:
        audit_log = generate_audit_log(flags, submission.user_name, exam.title)

    db_submission = Submission(
        exam_id=exam_id,
        user_name=submission.user_name.strip(),
        suspicious=is_suspicious,
        flag_reasons=",".join(flag_reasons) if flag_reasons else None,
        time_taken=submission.time_taken_seconds,
        answers=str(submission.answers),
        audit_log=audit_log,
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)

    return SubmissionResponse(
        id=db_submission.id,
        exam_id=db_submission.exam_id,
        user_name=db_submission.user_name,
        suspicious=db_submission.suspicious,
        flag_reasons=flag_reasons,
        time_taken_seconds=db_submission.time_taken,
        audit_log=db_submission.audit_log,
    )


@app.get("/submissions/", response_model=List[SubmissionResponse], tags=["Submissions"])
def list_submissions(flagged_only: bool = False, db: Session = Depends(get_db)):
    """List all submissions. Filter by flagged_only=true to see suspicious ones."""
    query = db.query(Submission)
    if flagged_only:
        query = query.filter(Submission.suspicious == True)
    subs = query.all()
    result = []
    for s in subs:
        reasons = s.flag_reasons.split(",") if s.flag_reasons else []
        result.append(SubmissionResponse(
            id=s.id,
            exam_id=s.exam_id,
            user_name=s.user_name,
            suspicious=s.suspicious,
            flag_reasons=reasons,
            time_taken_seconds=s.time_taken,
            audit_log=s.audit_log,
        ))
    return result


@app.get("/submissions/{submission_id}", response_model=SubmissionResponse, tags=["Submissions"])
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    """Get a specific submission by ID."""
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found.")
    reasons = s.flag_reasons.split(",") if s.flag_reasons else []
    return SubmissionResponse(
        id=s.id,
        exam_id=s.exam_id,
        user_name=s.user_name,
        suspicious=s.suspicious,
        flag_reasons=reasons,
        time_taken_seconds=s.time_taken,
    )


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "system": "Online Exam Proctoring System", "org": "aumne.ai"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
