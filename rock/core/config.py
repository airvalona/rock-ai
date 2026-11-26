from pathlib import Path
import json
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

DEFAULT_ROCK_DIR = Path.home() / ".rock"
CONFIG_FILE = DEFAULT_ROCK_DIR / "config.json"
WORKSPACE_DIR = DEFAULT_ROCK_DIR / "workspace"
DB_PATH = DEFAULT_ROCK_DIR / "rock.db"

class ModelConfig(BaseModel):
    provider: str = "openai"  # openai, anthropic, gemini, deepseek, xai, ollama, openrouter
    model_name: str = "gpt-4o"
    api_key: Optional[str] = None
    api_base: Optional[str] = None

class AgentRoleConfig(BaseModel):
    name: str
    role_title: str
    model: str = "default"
    temperature: float = 0.7
    system_prompt: str

class RockConfig(BaseModel):
    version: str = "0.1.0"
    workspace_path: str = str(WORKSPACE_DIR)
    default_model: str = "gpt-4o"
    providers: Dict[str, ModelConfig] = Field(default_factory=dict)
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_token: Optional[str] = None
    gateway_port: int = 8787
    safe_mode: bool = True

    @classmethod
    def load(cls) -> "RockConfig":
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                return cls()
        return cls()

    def save(self) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2)
