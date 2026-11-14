from typing import Optional
from .base import BaseAgent
from ..models.router import ModelRouter

CONTRARIAN_SYSTEM_PROMPT = """You are the Contrarian / Auditor of the rock.ai fleet.
Your responsibility is:
1. Challenge assumptions, stress-test logic, and identify edge cases or weaknesses.
2. Act as a relentless fact-checker to eliminate hallucinations and sloppy reasoning.
3. Review code for security flaws, performance bottlenecks, and failure modes.
4. Provide constructive criticism: point out what can break and how to harden it.
Never simply nod along. Be rigorous, analytical, and uncompromising in quality control.
"""

class ContrarianAgent(BaseAgent):
    def __init__(self, model: Optional[str] = None, router: Optional[ModelRouter] = None):
        super().__init__(
            name="Contrarian",
            role="Auditor, Critic & Fact-Checker",
            system_prompt=CONTRARIAN_SYSTEM_PROMPT,
            model=model,
            router=router
        )

    def audit(self, plan_or_work: str, goal: str) -> str:
        prompt = (
            f"Original Objective: {goal}\n\n"
            f"Proposed Solution / Work Done to Audit:\n{plan_or_work}\n\n"
            "Analyze this critically: What assumptions are questionable? "
            "What edge cases or security issues exist? How should this be refined or strengthened?"
        )
        return self.respond(prompt)
