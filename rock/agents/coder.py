from typing import Optional
from .base import BaseAgent
from ..models.router import ModelRouter
from ..tools.sandbox import SandboxManager
from ..tools.code_runner import CodeRunner

CODER_SYSTEM_PROMPT = """You are the Coder / Builder agent in the rock.ai multi-agent team.
Your responsibility is:
1. Write clean, robust, production-ready code, scripts, or configurations.
2. Inspect and modify project files inside the sandbox workspace.
3. Validate and execute code safely to ensure correctness before delivery.
Focus on efficiency, error handling, clean interfaces, and proper formatting.
"""

class CoderAgent(BaseAgent):
    def __init__(
        self,
        model: Optional[str] = None,
        router: Optional[ModelRouter] = None,
        sandbox: Optional[SandboxManager] = None
    ):
        super().__init__(
            name="Coder",
            role="Software Engineer & Tool Builder",
            system_prompt=CODER_SYSTEM_PROMPT,
            model=model,
            router=router
        )
        self.sandbox = sandbox or SandboxManager()
        self.runner = CodeRunner(sandbox=self.sandbox)

    def write_code(self, specification: str, context: Optional[str] = None) -> str:
        prompt = (
            f"Specification / Task:\n{specification}\n\n"
            "Provide the complete, bug-free implementation with clear explanations and inline comments."
        )
        return self.respond(prompt, context=context)

    def execute_and_test(self, python_code: str) -> str:
        res = self.runner.run_python(python_code)
        if res["success"]:
            return f"Code executed successfully.\nOutput:\n{res['stdout']}"
        else:
            return f"Execution error:\n{res['stderr']}"
