"""Database models, engine setup, and schema initialization."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from backend.app.config import settings

Base = declarative_base()


class Run(Base):
    """Execution run entity for candidate evaluation."""

    __tablename__ = "runs"

    id = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)
    cache_key = Column(String(128), index=True, nullable=True)

    decision = Column(String(32), nullable=True)
    council_score = Column(Float, nullable=True)
    base_score = Column(Float, nullable=True)
    quorum = Column(Boolean, nullable=True)
    veto = Column(Boolean, nullable=True)
    veto_signals = Column(Text, nullable=True)  # JSON list
    unresolved = Column(Integer, nullable=True)
    aar = Column(Float, nullable=True)
    error = Column(Text, nullable=True)

    inputs = relationship("RunInput", back_populates="run", uselist=False, cascade="all, delete-orphan")
    artifacts = relationship("RunArtifact", back_populates="run", cascade="all, delete-orphan")
    llm_calls = relationship("LLMCall", back_populates="run", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="run", cascade="all, delete-orphan")


class RunInput(Base):
    """Redacted inputs for a run. Never stores raw PII or candidate names."""

    __tablename__ = "run_inputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, unique=True, index=True)
    jd = Column(Text, nullable=False)
    resume_redacted = Column(Text, nullable=False)
    transcript_redacted = Column(Text, nullable=False)
    input_hash = Column(String(128), index=True, nullable=False)

    run = relationship("Run", back_populates="inputs")


class RunArtifact(Base):
    """Serialized JSON artifacts from pipeline execution."""

    __tablename__ = "run_artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, index=True)
    artifact_type = Column(String(64), nullable=False)  # evals, points, gate, chair, trace, etc.
    content = Column(Text, nullable=False)  # JSON or text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="artifacts")


class LLMCall(Base):
    """Audit log of individual LLM calls made during a run."""

    __tablename__ = "llm_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False)
    provider = Column(String(32), nullable=False)
    model = Column(String(128), nullable=False)
    tokens = Column(Integer, default=0, nullable=False)
    latency = Column(Float, default=0.0, nullable=False)
    finish_reason = Column(String(32), nullable=True)
    retries = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="llm_calls")


class Review(Base):
    """Human decision record for an evaluation run."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, index=True)
    decision = Column(String(32), nullable=False)  # ADVANCE, REVIEW, DO_NOT_ADVANCE
    reviewer = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="reviews")


_ENGINE = None
_SESSION_FACTORY = None


def get_engine(db_url: str | None = None):
    """Get or create the SQLAlchemy engine."""
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is None or db_url is not None:
        url = db_url or settings.DATABASE_URL
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _ENGINE = create_engine(url, connect_args=connect_args)
        _SESSION_FACTORY = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)
    return _ENGINE


def get_session():
    """Get a new database session."""
    get_engine()
    assert _SESSION_FACTORY is not None
    return _SESSION_FACTORY()


def get_db():
    """FastAPI database session dependency."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def init_db(engine=None) -> None:
    """Create all database tables."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
