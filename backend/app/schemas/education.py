from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class QuizQuestionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_index: int
    question: str
    options: List[str]
    correct_option_index: int
    explanation: str

class QuizSubmissionRequest(BaseModel):
    user_session_id: Optional[str] = None
    answers: dict[int, int] # question_id -> chosen option index

class QuizResultResponse(BaseModel):
    score: int
    total: int
    percentage: float
    passed: bool
    results: List[dict]

class LearningModuleListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    order_index: int
    title: str
    subtitle: Optional[str] = None
    category: str
    estimated_minutes: int
    level: str
    is_completed: Optional[bool] = False

class LearningModuleDetailSchema(LearningModuleListSchema):
    concept_explanation: str
    why_it_matters: str
    practical_indian_example: str
    common_mistakes: List[str] = []
    key_takeaways: List[str] = []
    official_source_links: List[dict] = []
    quizzes: List[QuizQuestionSchema] = []
