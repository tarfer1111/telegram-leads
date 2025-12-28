# backend/app/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

project_managers = Table(
    'project_managers',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    managers = relationship("User", secondary=project_managers, back_populates="projects")
    bots = relationship("Bot", back_populates="project")
    leads = relationship("Lead", back_populates="project")
    counters = relationship("DistributionCounter", back_populates="project")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", secondary=project_managers, back_populates="managers")
    leads = relationship("Lead", back_populates="manager")


class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    token = Column(String, nullable=False)
    auto_reply = Column(Text, nullable=False)
    webhook_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    project = relationship("Project", back_populates="bots")
    leads = relationship("Lead", back_populates="bot")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    telegram_chat_id = Column(BigInteger, unique=True, nullable=False)
    telegram_username = Column(String, nullable=True)
    telegram_first_name = Column(String, nullable=True)
    telegram_last_name = Column(String, nullable=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assigned_manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="new")  # new, read, in_progress, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    bot = relationship("Bot", back_populates="leads")
    project = relationship("Project", back_populates="leads")
    manager = relationship("User", back_populates="leads")
    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    sender = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="messages")


class DistributionCounter(Base):
    __tablename__ = "distribution_counters"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True, nullable=False)
    counter = Column(Integer, default=0)

    project = relationship("Project", back_populates="counters")