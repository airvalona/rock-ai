import json
import re
from typing import Optional, Dict, Any
from .base import BaseAgent
from ..models.router import ModelRouter

CAPTAIN_SYSTEM_PROMPT = """You are the Captain of the rock.ai multi-agent team.
Your responsibility is:
1. Understand the user's objective thoroughly.
2. Break down complex tasks into subtasks for the Researcher, Coder, or specialized custom agents.
3. Coordinate intermediate outputs and internal team debate.
4. Dynamically recruit and spawn new specialized coworker agents when requested by the user.
5. Synthesize verified insights into a clear, cohesive, actionable response for the user.
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

    def analyze_agent_spawn_request(self, message: str) -> Optional[Dict[str, str]]:
        """
        Detects if the user wants to create/spawn a new agent.
        Returns a dict with name, role, system_prompt if requested, else None.
        """
        lower = message.lower()
        create_triggers = ["create an agent", "create a new agent", "create agent", "spawn an agent", "add an agent", "make an agent"]
        if not any(t in lower for t in create_triggers):
            return None

        # Heuristic extraction first
        match = re.search(r"(?:create|spawn|add|make)(?:\s+a|\s+an|\s+new)?\s+agent(?:\s+named|\s+called)?\s+([A-Za-z0-9_]+)", message, re.IGNORECASE)
        name = match.group(1).strip() if match else "Specialist"

        role = f"{name} Specialist"
        system_prompt = f"You are {name}, an autonomous specialist agent in the rock.ai fleet. Focus with high precision on: {message}"

        # If LLM is available, generate optimal role and detailed prompt
        try:
            prompt = (
                f"The user wants to spawn a new AI coworker agent. User request: '{message}'.\n"
                "Respond ONLY with a JSON object with exactly these keys:\n"
                '{"name": "...", "role": "...", "system_prompt": "..."}'
            )
            raw = self.respond(prompt)
            # Find json block
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return {
                    "name": data.get("name", name),
                    "role": data.get("role", role),
                    "system_prompt": data.get("system_prompt", system_prompt)
                }
        except Exception:
            pass

        return {
            "name": name,
            "role": role,
            "system_prompt": system_prompt
        }
