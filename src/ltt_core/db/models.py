from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer)
    name = Column(String)
    functional_unit = Column(JSON)
    method = Column(JSON)

class LcaRun(Base):
    __tablename__ = "lca_runs"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer)
    score = Column(Float)
    run_at = Column(DateTime, default=datetime.utcnow)