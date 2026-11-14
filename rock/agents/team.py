from typing import Dict, Any, Optional, Callable, List
from .captain import CaptainAgent
from .researcher import ResearcherAgent
from .coder import CoderAgent
from .contrarian import ContrarianAgent
from ..models.router import ModelRouter
from ..core.config import RockConfig

class AgentTeam:
    """
    Coordinates the rock.ai fleet: Captain, Researcher, Coder, and Contrarian.
    Supports both Hierarchical Multi-Agent Debate and Autonomous Group Chat.
    """

    def __init__(self, config: Optional[RockConfig] = None):
        self.config = config or RockConfig.load()
        self.router = ModelRouter(config=self.config)

        self.captain = CaptainAgent(router=self.router)
        self.researcher = ResearcherAgent(router=self.router)
        self.coder = CoderAgent(router=self.router)
        self.contrarian = ContrarianAgent(router=self.router)

        self.agents = {
            "captain": self.captain,
            "researcher": self.researcher,
            "coder": self.coder,
            "contrarian": self.contrarian,
        }

    def execute_goal(
        self,
        goal: str,
        on_step: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes a goal using the Grok Bot 4-agent internal debate pipeline:
        1. Captain plans and delegates
        2. Researcher gathers context
        3. Coder drafts/executes
        4. Contrarian audits and red-teams
        5. Captain synthesizes final consensus
        """
        def log(agent_name: str, message: str):
            if on_step:
                on_step(agent_name, message)

        # Step 1: Captain breaks down the problem
        log("Captain", "Analyzing objective and organizing workflow...")
        plan = self.captain.plan_subtasks(goal)
        log("Captain", f"Plan outlined:\n{plan[:300]}...")

        # Step 2: Researcher gathers facts & intelligence
        log("Researcher", "Investigating external sources and documentation...")
        research_notes = self.researcher.research(goal)
        log("Researcher", f"Research compiled:\n{research_notes[:300]}...")

        # Step 3: Coder implements or drafts technical components
        log("Coder", "Developing technical response / code assets...")
        coder_output = self.coder.write_code(
            specification=goal,
            context=f"Plan:\n{plan}\n\nResearch:\n{research_notes}"
        )
        log("Coder", f"Work completed:\n{coder_output[:300]}...")

        # Step 4: Contrarian audits work for flaws and hallucinations
        log("Contrarian", "Stress-testing findings, checking edge cases and accuracy...")
        audit = self.contrarian.audit(
            plan_or_work=f"Research:\n{research_notes}\n\nCode/Output:\n{coder_output}",
            goal=goal
        )
        log("Contrarian", f"Audit feedback:\n{audit[:300]}...")

        # Step 5: Captain synthesizes final consensus
        log("Captain", "Synthesizing team insights into final consensus output...")
        final_answer = self.captain.synthesize(
            user_goal=goal,
            team_notes=f"Research:\n{research_notes}\n\nEngineering:\n{coder_output}",
            audit_feedback=audit
        )
        log("Captain", "Task successfully completed.")

        return {
            "goal": goal,
            "final_answer": final_answer,
            "debate": {
                "plan": plan,
                "research": research_notes,
                "coder_output": coder_output,
                "audit": audit
            }
        }

    def group_chat(self, message: str) -> Dict[str, str]:
        """
        Processes a chat message in group chat mode.
        Supports explicit @agent tags or routes to Captain by default.
        """
        lower = message.lower()
        if "@researcher" in lower:
            agent = self.researcher
            tag = "Researcher"
        elif "@coder" in lower:
            agent = self.coder
            tag = "Coder"
        elif "@contrarian" in lower:
            agent = self.contrarian
            tag = "Contrarian"
        else:
            agent = self.captain
            tag = "Captain"

        reply = agent.respond(message)
        return {"agent": tag, "reply": reply}
