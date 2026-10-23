from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel

class LearningModule(TimeStampedModel):
    __tablename__ = "learning_modules"
    
    slug = Column(String(100), unique=True, index=True, nullable=False)
    order_index = Column(Integer, default=1, index=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(255), nullable=True)
    category = Column(String(50), default="Basics") # Basics, Health, Life, Motor, Claims, Consumer Protection
    estimated_minutes = Column(Integer, default=8)
    level = Column(String(20), default="Beginner") # Beginner, Intermediate, Advanced
    
    # Core educational components
    concept_explanation = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=False)
    practical_indian_example = Column(Text, nullable=False)
    common_mistakes = Column(JSON, default=list) # List of misconceptions & traps
    key_takeaways = Column(JSON, default=list) # Bullet points of core rules
    official_source_links = Column(JSON, default=list) # Links to IRDAI, Bima Bharosa, GIC
    
    quizzes = relationship("QuizQuestion", back_populates="module", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")

class QuizQuestion(TimeStampedModel):
    __tablename__ = "quiz_questions"
    
    module_id = Column(Integer, ForeignKey("learning_modules.id"), nullable=False)
    order_index = Column(Integer, default=1)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False) # List of 4 string options
    correct_option_index = Column(Integer, nullable=False) # 0 to 3
    explanation = Column(Text, nullable=False) # Why this answer is correct & real-life lesson
    
    module = relationship("LearningModule", back_populates="quizzes")
