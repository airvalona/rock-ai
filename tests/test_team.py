import pytest
from unittest.mock import MagicMock
from rock.agents.team import AgentTeam
from rock.core.config import RockConfig

def test_agent_team_group_chat_mentions():
    cfg = RockConfig()
    team = AgentTeam(config=cfg)

    team.researcher.respond = MagicMock(return_value="Researcher findings.")
    team.coder.respond = MagicMock(return_value="Coder script.")
    team.contrarian.respond = MagicMock(return_value="Contrarian critique.")
    team.captain.respond = MagicMock(return_value="Captain direction.")

    r1 = team.group_chat("@researcher look up latest docs")
    assert r1["agent"] == "Researcher"
    assert r1["reply"] == "Researcher findings."

    r2 = team.group_chat("@coder write a python function")
    assert r2["agent"] == "Coder"
    assert r2["reply"] == "Coder script."

    r3 = team.group_chat("@contrarian check this plan")
    assert r3["agent"] == "Contrarian"
    assert r3["reply"] == "Contrarian critique."

    r4 = team.group_chat("What should we do next?")
    assert r4["agent"] == "Captain"
    assert r4["reply"] == "Captain direction."
