from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from config.settings import settings

Base = declarative_base()


class JobRecord(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    portal = Column(String(50), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    match_score = Column(Float, default=0.0)
    resume_type = Column(String(50), default="java")
    status = Column(String(50), default="DISCOVERED")
    screenshot_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, nullable=True)
    event = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Engine & Session
engine = create_engine(settings.DATABASE_URL, echo=False)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseManager:
    @staticmethod
    def save_job(title: str, company: str, portal: str, url: str, match_score: float = 0.0, resume_type: str = "java") -> int:
        session = SessionLocal()
        try:
            existing = session.query(JobRecord).filter(JobRecord.url == url).first()
            if existing:
                return existing.id

            record = JobRecord(
                title=title,
                company=company,
                portal=portal,
                url=url,
                match_score=match_score,
                resume_type=resume_type,
                status="QUEUED"
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id
        finally:
            session.close()

    @staticmethod
    def update_job_status(url: str, status: str, screenshot_path: Optional[str] = None):
        session = SessionLocal()
        try:
            job = session.query(JobRecord).filter(JobRecord.url == url).first()
            if job:
                job.status = status
                if screenshot_path:
                    job.screenshot_path = screenshot_path
                if status == "APPLIED":
                    job.applied_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    @staticmethod
    def list_recent_jobs(limit: int = 20) -> List[JobRecord]:
        session = SessionLocal()
        try:
            return session.query(JobRecord).order_by(JobRecord.id.desc()).limit(limit).all()
        finally:
            session.close()


db = DatabaseManager()
