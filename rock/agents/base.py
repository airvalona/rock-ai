from typing import List, Dict, Any, Optional
from ..models.router import ModelRouter
from ..core.config import RockConfig

class BaseAgent:
    """
    Base class for autonomous specialized agents in the rock.ai fleet.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: Optional[str] = None,
        router: Optional[ModelRouter] = None
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.router = router or ModelRouter()
        self.history: List[Dict[str, str]] = []

    def respond(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generates an agent response given a prompt and optional background context.
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        if context:
            messages.append({"role": "system", "content": f"Shared Context / Team Notes:\n{context}"})

        # Append recent interaction history
        for h in self.history[-6:]:
            messages.append(h)

        messages.append({"role": "user", "content": prompt})

        try:
            reply = self.router.complete(
                messages=messages,
                model=self.model
            )
        except Exception as e:
            err_msg = str(e)
            target_model = self.model or self.router.config.default_model
            if "api_key" in err_msg.lower() or "auth" in err_msg.lower() or "authentication" in err_msg.lower():
                reply = (
                    f"⚠️ **[API Key Required]**\n\n"
                    f"Could not connect to model `{target_model}` because no valid API key was found.\n\n"
                    f"**How to configure:**\n"
                    f"1. Run `rock onboard` in your terminal to set your provider keys, OR\n"
                    f"2. Add your API key directly to `~/.rock/config.json`."
                )
            else:
                reply = f"⚠️ **[Error executing request with '{target_model}']**: {err_msg}"

        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": reply})

        return reply
