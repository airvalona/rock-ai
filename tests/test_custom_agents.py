import pytest
from pathlib import Path
from unittest.mock import MagicMock
from rock.core.database import DatabaseManager
from rock.agents.team import AgentTeam
from rock.core.config import RockConfig

def test_custom_agent_persistence_and_routing(tmp_path: Path):
    db_file = tmp_path / "test_agents.db"
    db = DatabaseManager(db_path=db_file)
    cfg = RockConfig()
    team = AgentTeam(config=cfg, db=db)

    # Register custom agent
    rec = team.register_custom_agent(
        name="Copywriter",
        role="Conversion Copy Specialist",
        system_prompt="You write compelling copy.",
        created_by="user"
    )
    assert rec.name == "Copywriter"
    assert "copywriter" in team.agents

    # Mock custom agent response
    team.agents["copywriter"].respond = MagicMock(return_value="Headline crafted!")

    # Test routing via @mention
    res = team.group_chat("@copywriter write a headline")
    assert res["agent"] == "Copywriter"
    assert res["reply"] == "Headline crafted!"

    # Test persistence on fresh team reload
    new_team = AgentTeam(config=cfg, db=db)
    assert "copywriter" in new_team.agents
    assert new_team.agents["copywriter"].role == "Conversion Copy Specialist"

    # Test deletion
    deleted = new_team.delete_custom_agent("Copywriter")
    assert deleted is True
    assert "copywriter" not in new_team.agents
