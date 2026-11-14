import os
from typing import List, Dict, Any, Optional
from ..core.config import RockConfig

# Use local cost map and disable verbose debug logs
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

try:
    import litellm
    # Suppress verbose litellm logs
    litellm.suppress_debug_info = True
except ImportError:
    litellm = None

class ModelRouter:
    """
    Universal Model Router supporting OpenAI, Anthropic, Gemini, DeepSeek,
    xAI Grok, Ollama, and OpenRouter through a unified interface.
    """

    def __init__(self, config: Optional[RockConfig] = None):
        self.config = config or RockConfig.load()
        self._setup_env()

    def _setup_env(self):
        """Set environment keys from rock config if present."""
        for provider_name, provider_cfg in self.config.providers.items():
            if not provider_cfg.api_key:
                continue
            p = provider_name.lower()
            if "openai" in p:
                os.environ["OPENAI_API_KEY"] = provider_cfg.api_key
            elif "anthropic" in p or "claude" in p:
                os.environ["ANTHROPIC_API_KEY"] = provider_cfg.api_key
            elif "gemini" in p or "google" in p:
                os.environ["GEMINI_API_KEY"] = provider_cfg.api_key
            elif "deepseek" in p:
                os.environ["DEEPSEEK_API_KEY"] = provider_cfg.api_key
            elif "grok" in p or "xai" in p:
                os.environ["XAI_API_KEY"] = provider_cfg.api_key
            elif "openrouter" in p:
                os.environ["OPENROUTER_API_KEY"] = provider_cfg.api_key

    def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """
        Dispatches completion requests to the specified model via LiteLLM.
        """
        target_model = model or self.config.default_model

        # Map friendly model shortcuts
        if target_model.startswith("gemini/") or "gemini" in target_model.lower():
            if not target_model.startswith("gemini/"):
                target_model = f"gemini/{target_model}"
        elif target_model.startswith("deepseek/") or "deepseek" in target_model.lower():
            if not target_model.startswith("deepseek/"):
                target_model = f"deepseek/{target_model}"

        if litellm is None:
            raise RuntimeError(
                "litellm is not installed. Run 'pip install litellm' to enable model routing."
            )

        try:
            response = litellm.completion(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            # Provide clean, actionable error diagnostics
            raise RuntimeError(f"Model dispatch to '{target_model}' failed: {str(e)}") from e
