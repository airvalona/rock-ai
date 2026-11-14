import pytest
from pathlib import Path
from rock.core.database import DatabaseManager

def test_database_task_and_cron(tmp_path: Path):
    db_file = tmp_path / "test_rock.db"
    db = DatabaseManager(db_path=db_file)

    # Test Task creation and completion
    task = db.create_task("Test task goal")
    assert task.id is not None
    assert task.status == "pending"

    db.update_task_completed(task.id, "Final synthesized output")
    tasks = db.list_tasks(limit=5)
    assert len(tasks) == 1
    assert tasks[0].status == "completed"
    assert tasks[0].final_answer == "Final synthesized output"

    # Test Cron job registration
    job = db.add_cron_job(name="Daily Check", cron_expr="0 8 * * *", goal="Check system status")
    assert job.id is not None
    cron_jobs = db.list_cron_jobs()
    assert len(cron_jobs) == 1
    assert cron_jobs[0].name == "Daily Check"
