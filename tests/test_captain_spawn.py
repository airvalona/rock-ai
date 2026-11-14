import pytest
from pathlib import Path
from rock.core.database import DatabaseManager
from rock.agents.team import AgentTeam
from rock.core.config import RockConfig

def test_captain_meta_agent_spawning(tmp_path: Path):
    db_file = tmp_path / "test_spawn.db"
    db = DatabaseManager(db_path=db_file)
    cfg = RockConfig()
    team = AgentTeam(config=cfg, db=db)

    # User message asking Captain to create an agent
    msg = "Captain, create an agent named SEOExpert to optimize metadata"
    res = team.group_chat(msg)

    assert res["agent"] == "Captain"
    assert "New Agent Recruited & Activated" in res["reply"]
    assert "@SEOExpert" in res["reply"]

    # Verify agent is immediately in active fleet
    assert "seoexpert" in team.agents
    assert team.agents["seoexpert"].name == "SEOExpert"

    # Verify persisted in database
    db_agents = db.list_agents()
    assert any(a.name == "SEOExpert" for a in db_agents)
