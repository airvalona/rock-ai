import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from ..core.config import RockConfig, ModelConfig, CONFIG_FILE, WORKSPACE_DIR

console = Console()

BANNER = """
[bold cyan]
  ____   ___   ____ _  __     _    ___ 
 |  _ \\ / _ \\ / ___| |/ /    / \\  |_ _|
 | |_) | | | | |   | ' /    / _ \\  | | 
 |  _ <| |_| | |___| . \\   / ___ \\ | | 
 |_| \\_\\\\___/ \\____|_|\\_\\ /_/   \\_\\___|
[/bold cyan]
[dim]Autonomous 24/7 Persistent Multi-Agent Fleet[/dim]
"""

def run_onboarding():
    """
    Interactive terminal onboarding wizard.
    """
    console.print(BANNER)
    console.print(Panel("[bold green]Welcome to rock.ai Setup Wizard![/bold green]\nConfigure your persistent agent fleet in seconds.", border_style="cyan"))

    cfg = RockConfig.load()

    # Step 1: Workspace setup
    workspace_str = inquirer.text(
        message="Workspace sandbox directory path:",
        default=str(WORKSPACE_DIR)
    ).execute()
    cfg.workspace_path = workspace_str
    Path(workspace_str).mkdir(parents=True, exist_ok=True)

    # Step 2: Choose primary AI provider
    provider = inquirer.select(
        message="Select your primary AI model provider:",
        choices=[
            Choice("openai", "OpenAI (GPT-4o, o3-mini)"),
            Choice("anthropic", "Anthropic Claude (Claude 3.7 Sonnet)"),
            Choice("gemini", "Google Gemini (Gemini 2.5 Flash / Pro)"),
            Choice("deepseek", "DeepSeek (DeepSeek V3 / R1)"),
            Choice("xai", "xAI (Grok 2 / Grok Beta)"),
            Choice("openrouter", "OpenRouter (Multi-model aggregator)"),
            Choice("ollama", "Local Ollama (Llama 3, Mistral, Qwen)"),
        ],
        default="openai"
    ).execute()

    # Step 3: Enter API Key (if not ollama)
    api_key = None
    if provider != "ollama":
        api_key = inquirer.secret(
            message=f"Enter your {provider.capitalize()} API key:"
        ).execute()

    # Model name mapping
    default_models = {
        "openai": "gpt-4o",
        "anthropic": "claude-3-7-sonnet-20250219",
        "gemini": "gemini/gemini-2.5-flash",
        "deepseek": "deepseek/deepseek-chat",
        "xai": "xai/grok-2-latest",
        "openrouter": "openrouter/auto",
        "ollama": "ollama/llama3"
    }

    model_name = inquirer.text(
        message="Default model identifier:",
        default=default_models.get(provider, "gpt-4o")
    ).execute()

    cfg.default_model = model_name
    cfg.providers[provider] = ModelConfig(
        provider=provider,
        model_name=model_name,
        api_key=api_key
    )

    # Step 4: Telegram Mobile Remote (Optional)
    setup_tg = inquirer.confirm(
        message="Would you like to set up Telegram Bot for 24/7 mobile control?",
        default=False
    ).execute()

    if setup_tg:
        tg_token = inquirer.secret(
            message="Paste your Telegram Bot Token (from @BotFather):"
        ).execute()
        cfg.telegram_token = tg_token

    # Step 5: Save Configuration
    cfg.save()

    console.print("\n[bold green][OK] Configuration successfully saved to ~/.rock/config.json![/bold green]\n")
    console.print(Panel(
        "[bold cyan]Quickstart Commands:[/bold cyan]\n"
        "• [bold white]rock chat[/bold white]          - Chat with your agent team in terminal\n"
        "• [bold white]rock daemon start[/bold white]  - Launch 24/7 background gateway & scheduler\n"
        "• [bold white]rock doctor[/bold white]        - Verify keys, database, and connections\n"
        "• [bold white]rock team[/bold white]          - View agent roster & assigned roles",
        title="Ready to rock!",
        border_style="green"
    ))
