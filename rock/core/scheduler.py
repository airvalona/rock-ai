from typing import Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .database import DatabaseManager
from ..agents.team import AgentTeam
from ..core.config import RockConfig

class AutonomousScheduler:
    """
    24/7 background job scheduler for recurring agent tasks.
    """

    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        team: Optional[AgentTeam] = None,
        config: Optional[RockConfig] = None
    ):
        self.db = db or DatabaseManager()
        self.team = team or AgentTeam(config=config)
        self.config = config or RockConfig.load()
        self.scheduler = BackgroundScheduler()
        self.on_job_completed: Optional[Callable[[str, str], None]] = None

    def start(self):
        """Starts the scheduler and loads persistent cron jobs from database."""
        self._load_jobs()
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    def _load_jobs(self):
        jobs = self.db.list_cron_jobs()
        for j in jobs:
            if j.enabled:
                self.add_job(j.id, j.name, j.cron_expression, j.goal)

    def add_job(self, job_id: int, name: str, cron_expr: str, goal: str):
        # cron_expr e.g. "0 9 * * *"
        fields = cron_expr.split()
        if len(fields) == 5:
            trigger = CronTrigger(
                minute=fields[0],
                hour=fields[1],
                day=fields[2],
                month=fields[3],
                day_of_week=fields[4]
            )
        else:
            # default fallback: every hour
            trigger = CronTrigger(minute="0")

        def run():
            task_rec = self.db.create_task(goal=f"[Scheduled: {name}] {goal}")
            res = self.team.execute_goal(goal)
            self.db.update_task_completed(task_rec.id, res["final_answer"])
            if self.on_job_completed:
                self.on_job_completed(name, res["final_answer"])

        self.scheduler.add_job(
            run,
            trigger=trigger,
            id=f"job_{job_id}",
            replace_existing=True
        )
