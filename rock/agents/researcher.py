from typing import Optional, List, Dict
from .base import BaseAgent
from ..models.router import ModelRouter
from ..tools.web import WebTools

RESEARCHER_SYSTEM_PROMPT = """You are the Researcher agent of the rock.ai multi-agent fleet.
Your responsibility is:
1. Gather accurate, up-to-date information, documentation, and facts.
2. Formulate targeted search queries to extract relevant data.
3. Distill complex findings into structured, cited notes for the Captain and Coder.
Be meticulous, objective, and cite your sources.
"""

class ResearcherAgent(BaseAgent):
    def __init__(self, model: Optional[str] = None, router: Optional[ModelRouter] = None):
        super().__init__(
            name="Researcher",
            role="Information & Web Intelligence",
            system_prompt=RESEARCHER_SYSTEM_PROMPT,
            model=model,
            router=router
        )
        self.web = WebTools()

    def research(self, topic: str) -> str:
        # Perform live search query
        results = self.web.search(topic, max_results=4)
        snippets = "\n".join([f"- [{r['title']}]({r['href']}): {r['body']}" for r in results])

        prompt = (
            f"Topic to investigate: {topic}\n\n"
            f"Search Snippets Found:\n{snippets}\n\n"
            "Analyze and summarize the key findings, data points, and technical details."
        )
        return self.respond(prompt)
