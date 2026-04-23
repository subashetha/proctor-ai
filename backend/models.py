from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from database import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  # minutes


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    user_name = Column(String, nullable=False)
    suspicious = Column(Boolean, default=False)
    flag_reasons = Column(Text, nullable=True)   # comma-separated
    time_taken = Column(Integer, nullable=True)  # seconds
    answers = Column(Text, nullable=True)        # raw answers dict as string
    audit_log = Column(Text, nullable=True)      # AI-generated explanation
