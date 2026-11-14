import datetime
from pathlib import Path
from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session, select
from .config import DB_PATH, DEFAULT_ROCK_DIR

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

class TaskRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    goal: str
    status: str = "pending"  # pending, in_progress, completed, failed
    final_answer: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime.datetime] = None

class CronJobRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cron_expression: str  # e.g. "0 9 * * *"
    goal: str
    enabled: bool = True
    last_run: Optional[datetime.datetime] = None

class AgentRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    role: str
    system_prompt: str
    model: Optional[str] = None
    created_by: str = "user"  # "user" or "captain"
    created_at: datetime.datetime = Field(default_factory=utc_now)

class ChatRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = "default"
    sender: str
    agent_name: Optional[str] = None
    message: str
    created_at: datetime.datetime = Field(default_factory=utc_now)

class DatabaseManager:
    """
    Manages SQLite persistence for tasks, cron schedules, and conversation history.
    """

    def __init__(self, db_path: Optional[Path] = None):
        DEFAULT_ROCK_DIR.mkdir(parents=True, exist_ok=True)
        path = db_path or DB_PATH
        self.engine = create_engine(f"sqlite:///{path}", echo=False)
        SQLModel.metadata.create_all(self.engine)

    def create_task(self, goal: str) -> TaskRecord:
        with Session(self.engine) as session:
            task = TaskRecord(goal=goal, status="pending")
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def update_task_completed(self, task_id: int, final_answer: str) -> None:
        with Session(self.engine) as session:
            task = session.get(TaskRecord, task_id)
            if task:
                task.status = "completed"
                task.final_answer = final_answer
                task.completed_at = utc_now()
                session.add(task)
                session.commit()

    def list_tasks(self, limit: int = 10) -> List[TaskRecord]:
        with Session(self.engine) as session:
            statement = select(TaskRecord).order_by(TaskRecord.id.desc()).limit(limit)
            return list(session.exec(statement).all())

    def save_chat(self, session_id: str, sender: str, message: str, agent_name: Optional[str] = None) -> None:
        with Session(self.engine) as session:
            record = ChatRecord(session_id=session_id, sender=sender, message=message, agent_name=agent_name)
            session.add(record)
            session.commit()

    def add_cron_job(self, name: str, cron_expr: str, goal: str) -> CronJobRecord:
        with Session(self.engine) as session:
            job = CronJobRecord(name=name, cron_expression=cron_expr, goal=goal, enabled=True)
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def list_cron_jobs(self) -> List[CronJobRecord]:
        with Session(self.engine) as session:
            statement = select(CronJobRecord)
            return list(session.exec(statement).all())

    def save_agent(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: Optional[str] = None,
        created_by: str = "user"
    ) -> AgentRecord:
        with Session(self.engine) as session:
            statement = select(AgentRecord).where(AgentRecord.name == name)
            existing = session.exec(statement).first()
            if existing:
                existing.role = role
                existing.system_prompt = system_prompt
                existing.model = model
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                agent = AgentRecord(
                    name=name,
                    role=role,
                    system_prompt=system_prompt,
                    model=model,
                    created_by=created_by
                )
                session.add(agent)
                session.commit()
                session.refresh(agent)
                return agent

    def list_agents(self) -> List[AgentRecord]:
        with Session(self.engine) as session:
            statement = select(AgentRecord).order_by(AgentRecord.name.asc())
            return list(session.exec(statement).all())

    def delete_agent(self, name: str) -> bool:
        with Session(self.engine) as session:
            statement = select(AgentRecord).where(AgentRecord.name == name)
            agent = session.exec(statement).first()
            if agent:
                session.delete(agent)
                session.commit()
                return True
            return False
