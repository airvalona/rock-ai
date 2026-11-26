from typing import Dict, Any, Optional, Callable, List
from .base import BaseAgent
from .captain import CaptainAgent
from .researcher import ResearcherAgent
from .coder import CoderAgent
from .contrarian import ContrarianAgent
from ..models.router import ModelRouter
from ..core.config import RockConfig
from ..core.database import DatabaseManager, AgentRecord

class AgentTeam:
    """
    Coordinates the rock.ai fleet: Captain, Researcher, Coder, Contrarian,
    and dynamically registered custom agents.
    Supports both Hierarchical Multi-Agent Debate and Autonomous Group Chat.
    """

    def __init__(self, config: Optional[RockConfig] = None, db: Optional[DatabaseManager] = None):
        self.config = config or RockConfig.load()
        self.db = db or DatabaseManager()
        self.router = ModelRouter(config=self.config)

        self.captain = CaptainAgent(router=self.router)
        self.researcher = ResearcherAgent(router=self.router)
        self.coder = CoderAgent(router=self.router)
        self.contrarian = ContrarianAgent(router=self.router)

        self.agents: Dict[str, BaseAgent] = {
            "captain": self.captain,
            "researcher": self.researcher,
            "coder": self.coder,
            "contrarian": self.contrarian,
        }

        self.on_event: Optional[Callable[[Dict[str, Any]], None]] = None
        self._load_custom_agents()

    def _load_custom_agents(self):
        """Loads persistent custom agents from the database into the active roster."""
        custom_records = self.db.list_agents()
        for rec in custom_records:
            agent = BaseAgent(
                name=rec.name,
                role=rec.role,
                system_prompt=rec.system_prompt,
                model=rec.model or self.config.default_model,
                router=self.router
            )
            self.agents[rec.name.lower()] = agent

    def register_custom_agent(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: Optional[str] = None,
        created_by: str = "user"
    ) -> AgentRecord:
        """Dynamically registers and persists a custom agent."""
        clean_name = name.strip()
        record = self.db.save_agent(
            name=clean_name,
            role=role,
            system_prompt=system_prompt,
            model=model or self.config.default_model,
            created_by=created_by
        )
        agent = BaseAgent(
            name=clean_name,
            role=role,
            system_prompt=system_prompt,
            model=model or self.config.default_model,
            router=self.router
        )
        self.agents[clean_name.lower()] = agent

        if self.on_event:
            self.on_event({
                "type": "agent_created",
                "name": clean_name,
                "role": role,
                "created_by": created_by
            })

        return record

    def delete_custom_agent(self, name: str) -> bool:
        clean_name = name.strip().lower()
        if clean_name in ("captain", "researcher", "coder", "contrarian"):
            return False  # Built-ins cannot be deleted
        success = self.db.delete_agent(name)
        if clean_name in self.agents:
            del self.agents[clean_name]
        return success

    def list_roster(self) -> List[Dict[str, Any]]:
        roster = []
        for k, a in self.agents.items():
            is_builtin = k in ("captain", "researcher", "coder", "contrarian")
            roster.append({
                "name": a.name,
                "role": a.role,
                "model": a.model or self.config.default_model,
                "is_builtin": is_builtin
            })
        return roster

    def execute_goal(
        self,
        goal: str,
        on_step: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes a goal using the collaborative 4-agent internal debate pipeline.
        """
        def log(agent_name: str, message: str, step_type: str = "log"):
            if on_step:
                on_step(agent_name, message)
            if self.on_event:
                self.on_event({
                    "type": "agent_step",
                    "agent": agent_name,
                    "message": message,
                    "step_type": step_type
                })

        # Step 1: Captain breaks down the problem
        log("Captain", "Analyzing objective and organizing workflow...", "plan")
        plan = self.captain.plan_subtasks(goal)
        log("Captain", f"Plan outlined:\n{plan[:300]}...", "plan")

        # Step 2: Researcher gathers facts & intelligence
        log("Researcher", "Investigating external sources and documentation...", "research")
        research_notes = self.researcher.research(goal)
        log("Researcher", f"Research compiled:\n{research_notes[:300]}...", "research")

        # Step 3: Coder implements or drafts technical components
        log("Coder", "Developing technical response / code assets...", "code")
        coder_output = self.coder.write_code(
            specification=goal,
            context=f"Plan:\n{plan}\n\nResearch:\n{research_notes}"
        )
        log("Coder", f"Work completed:\n{coder_output[:300]}...", "code")

        # Step 4: Contrarian audits work for flaws and hallucinations
        log("Contrarian", "Stress-testing findings, checking edge cases and accuracy...", "audit")
        audit = self.contrarian.audit(
            plan_or_work=f"Research:\n{research_notes}\n\nCode/Output:\n{coder_output}",
            goal=goal
        )
        log("Contrarian", f"Audit feedback:\n{audit[:300]}...", "audit")

        # Step 5: Captain synthesizes final consensus
        log("Captain", "Synthesizing team insights into final consensus output...", "synthesize")
        final_answer = self.captain.synthesize(
            user_goal=goal,
            team_notes=f"Research:\n{research_notes}\n\nEngineering:\n{coder_output}",
            audit_feedback=audit
        )
        log("Captain", "Task successfully completed.", "done")

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
        Supports explicit @agent tags, dynamic custom agents, or Captain's Meta-Agent spawning.
        """
        lower = message.lower()

        # Check if user is asking Captain to spawn an agent
        spawn_req = self.captain.analyze_agent_spawn_request(message)
        if spawn_req:
            rec = self.register_custom_agent(
                name=spawn_req["name"],
                role=spawn_req["role"],
                system_prompt=spawn_req["system_prompt"],
                created_by="captain"
            )
            reply = (
                f"🚀 **New Agent Recruited & Activated!**\n\n"
                f"I have created and registered **@{rec.name}** to our fleet roster.\n"
                f"• **Role**: {rec.role}\n"
                f"• **Instructions**: {rec.system_prompt[:180]}...\n\n"
                f"You can now mention `@{rec.name}` anytime to assign them specialized tasks!"
            )
            return {"agent": "Captain", "reply": reply}

        # Check for any @agent mention (built-in or custom)
        target_agent = self.captain
        tag = "Captain"

        for agent_key, agent_obj in self.agents.items():
            if f"@{agent_key}" in lower:
                target_agent = agent_obj
                tag = agent_obj.name
                break

        reply = target_agent.respond(message)
        return {"agent": tag, "reply": reply}
