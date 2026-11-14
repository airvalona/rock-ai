from typing import Optional
from .base import BaseAgent
from ..models.router import ModelRouter

CAPTAIN_SYSTEM_PROMPT = """You are the Captain of the rock.ai multi-agent team.
Your responsibility is:
1. Understand the user's objective thoroughly.
2. Break down complex tasks into subtasks for the Researcher and Coder.
3. Coordinate intermediate outputs and internal team debate.
4. Synthesize verified insights into a clear, cohesive, actionable response for the user.
Maintain a decisive, clear, and proactive leadership tone.
"""

class CaptainAgent(BaseAgent):
    def __init__(self, model: Optional[str] = None, router: Optional[ModelRouter] = None):
        super().__init__(
            name="Captain",
            role="Team Orchestrator & Synthesizer",
            system_prompt=CAPTAIN_SYSTEM_PROMPT,
            model=model,
            router=router
        )

    def plan_subtasks(self, user_goal: str) -> str:
        prompt = (
            f"Analyze this goal: '{user_goal}'. "
            "Outline specifically what information needs to be researched, "
            "what code or files need to be constructed, and what critical risks to check for."
        )
        return self.respond(prompt)

    def synthesize(self, user_goal: str, team_notes: str, audit_feedback: str) -> str:
        prompt = (
            f"Original User Goal: {user_goal}\n\n"
            f"Team Findings and Work Done:\n{team_notes}\n\n"
            f"Contrarian Audit & Verification:\n{audit_feedback}\n\n"
            "Now synthesize the final complete, polished response for the user, addressing all points directly."
        )
        return self.respond(prompt)
