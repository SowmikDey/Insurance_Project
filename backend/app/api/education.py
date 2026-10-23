from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.learning import LearningModule, QuizQuestion
from app.schemas.education import (
    LearningModuleListSchema,
    LearningModuleDetailSchema,
    QuizSubmissionRequest,
    QuizResultResponse
)

router = APIRouter(prefix="/education", tags=["education"])

@router.get("/modules", response_model=List[LearningModuleListSchema])
def list_learning_modules(db: Session = Depends(get_db)):
    modules = db.query(LearningModule).order_by(LearningModule.order_index.asc()).all()
    return modules

@router.get("/modules/{slug}", response_model=LearningModuleDetailSchema)
def get_module_detail(slug: str, db: Session = Depends(get_db)):
    m = db.query(LearningModule).filter(LearningModule.slug == slug).first()
    if not m:
        raise HTTPException(status_code=404, detail="Learning module not found")
    return m

@router.post("/quiz/submit", response_model=QuizResultResponse)
def submit_quiz(req: QuizSubmissionRequest, db: Session = Depends(get_db)):
    if not req.answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    question_ids = list(req.answers.keys())
    questions = db.query(QuizQuestion).filter(QuizQuestion.id.in_(question_ids)).all()

    correct_count = 0
    total = len(questions)
    results = []

    for q in questions:
        user_choice = req.answers.get(q.id)
        is_correct = (user_choice == q.correct_option_index)
        if is_correct:
            correct_count += 1
            
        results.append({
            "question_id": q.id,
            "question": q.question,
            "user_choice_index": user_choice,
            "correct_option_index": q.correct_option_index,
            "is_correct": is_correct,
            "explanation": q.explanation
        })

    percentage = round((correct_count / total * 100), 1) if total > 0 else 0
    passed = percentage >= 70.0

    return QuizResultResponse(
        score=correct_count,
        total=total,
        percentage=percentage,
        passed=passed,
        results=results
    )
