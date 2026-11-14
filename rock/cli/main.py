import typer
import webbrowser
import threading
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional
from pathlib import Path
from ..core.config import RockConfig, CONFIG_FILE, WORKSPACE_DIR, DB_PATH
from ..core.database import DatabaseManager
from ..core.gateway import GatewayService
from ..agents.team import AgentTeam
from .onboard import run_onboarding, BANNER

app = typer.Typer(help="rock.ai — Autonomous 24/7 Persistent Multi-Agent Fleet")
daemon_app = typer.Typer(help="Manage 24/7 background gateway daemon")
cron_app = typer.Typer(help="Manage autonomous recurring agent jobs")
agent_app = typer.Typer(help="Manage custom agent specialists")

app.add_typer(daemon_app, name="daemon")
app.add_typer(cron_app, name="cron")
app.add_typer(agent_app, name="agent")

console = Console()

@app.command()
def onboard():
    """Run interactive OpenClaw-style setup wizard."""
    run_onboarding()

@app.command()
def chat():
    """Interactive terminal chat session with the rock.ai agent team."""
    console.print(BANNER)
    cfg = RockConfig.load()
    if not CONFIG_FILE.exists():
        console.print("[yellow]No config found. Running onboarding first...[/yellow]")
        run_onboarding()
        cfg = RockConfig.load()

    team = AgentTeam(config=cfg)
    console.print(Panel(
        "[bold green]Connected to rock.ai Fleet![/bold green]\n"
        "• Default mode: Captain leads & delegates\n"
        "• Mentions: Tag [cyan]@researcher[/cyan], [cyan]@coder[/cyan], or [cyan]@contrarian[/cyan] for direct responses\n"
        "• Type [bold red]exit[/bold red] or [bold red]quit[/bold red] to end session.",
        border_style="cyan"
    ))

    while True:
        try:
            user_input = console.input("[bold green]You > [/bold green]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[dim]Goodbye![/dim]")
                break

            with console.status("[bold cyan]Agent team thinking...[/bold cyan]", spinner="dots"):
                res = team.group_chat(user_input)

            console.print(f"\n[bold magenta]{res['agent']}:[/bold magenta]")
            console.print(Markdown(res['reply']))
            console.print()
        except KeyboardInterrupt:
            console.print("\n[dim]Session closed.[/dim]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

@app.command()
def task(goal: str):
    """Run full 4-agent Grok Bot debate pipeline on a specific objective."""
    cfg = RockConfig.load()
    team = AgentTeam(config=cfg)
    db = DatabaseManager()

    console.print(Panel(f"[bold cyan]New Objective:[/bold cyan]\n{goal}", title="rock.ai Mission", border_style="cyan"))

    def on_step(agent: str, msg: str):
        color = {
            "Captain": "blue",
            "Researcher": "green",
            "Coder": "yellow",
            "Contrarian": "red"
        }.get(agent, "white")
        console.print(f"[{color}][{agent}][/{color}] {msg}")

    task_rec = db.create_task(goal)
    with console.status("[bold cyan]Executing multi-agent debate...[/bold cyan]", spinner="bouncingBar"):
        result = team.execute_goal(goal, on_step=on_step)

    db.update_task_completed(task_rec.id, result["final_answer"])

    console.print("\n" + "=" * 60)
    console.print(Panel(Markdown(result["final_answer"]), title="[bold green]Final Synthesized Output[/bold green]", border_style="green"))

@app.command()
def team():
    """Display the active agent fleet roster and assigned models."""
    cfg = RockConfig.load()
    team_inst = AgentTeam(config=cfg)
    roster = team_inst.list_roster()

    table = Table(title="rock.ai Active Agent Roster", border_style="cyan")
    table.add_column("Agent", style="bold cyan")
    table.add_column("Specialty", style="magenta")
    table.add_column("Type", style="yellow")
    table.add_column("Model Identifier", style="green")

    for a in roster:
        kind = "Built-in" if a["is_builtin"] else "Custom Specialist"
        table.add_row(f"@{a['name']}", a["role"], kind, a["model"])

    console.print(table)

@app.command()
def ui(port: int = typer.Option(8787, help="Port to launch GrokBot visual workspace")):
    """Launch GrokBot-style Localhost Visual Workspace in your browser."""
    console.print(BANNER)
    console.print(Panel(
        f"[bold green]Starting GrokBot-Style Localhost Workspace on http://localhost:{port}[/bold green]\n"
        "Opening your default browser automatically...",
        border_style="cyan"
    ))

    # Auto-open browser in 1 second
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    cfg = RockConfig.load()
    gateway = GatewayService(config=cfg)
    gateway.start(host="127.0.0.1", port=port)

@agent_app.command("list")
def agent_list():
    """List all registered agent specialists."""
    db = DatabaseManager()
    custom_agents = db.list_agents()
    
    table = Table(title="Custom Agent Specialists", border_style="cyan")
    table.add_column("Name", style="bold cyan")
    table.add_column("Role Title", style="magenta")
    table.add_column("Created By", style="yellow")

    if not custom_agents:
        console.print("[dim]No custom agents registered yet. Try 'rock agent create' or ask Captain in chat![/dim]")
        return

    for a in custom_agents:
        table.add_row(f"@{a.name}", a.role, a.created_by)

    console.print(table)

@agent_app.command("create")
def agent_create(
    name: str = typer.Option(..., prompt="Agent Tag Name (e.g. Copywriter, SEOExpert)"),
    role: str = typer.Option(..., prompt="Role Title (e.g. Conversion Copywriting Specialist)"),
    prompt: str = typer.Option(..., prompt="System Instructions")
):
    """Register a new custom agent specialist."""
    cfg = RockConfig.load()
    team_inst = AgentTeam(config=cfg)
    rec = team_inst.register_custom_agent(
        name=name,
        role=role,
        system_prompt=prompt,
        created_by="user"
    )
    console.print(f"[bold green][OK] Custom agent @{rec.name} ({rec.role}) registered and activated![/bold green]")

@agent_app.command("delete")
def agent_delete(name: str):
    """Delete a custom agent specialist."""
    cfg = RockConfig.load()
    team_inst = AgentTeam(config=cfg)
    success = team_inst.delete_custom_agent(name)
    if success:
        console.print(f"[bold green][OK] Agent @{name} deleted from fleet.[/bold green]")
    else:
        console.print(f"[bold red]Failed to delete agent @{name} (built-in agents cannot be deleted).[/bold red]")

@app.command()
def doctor():
    """Diagnose configuration, API keys, database, and workspace health."""
    console.print(BANNER)
    console.print("[bold cyan]Running rock.ai System Diagnostics...[/bold cyan]\n")

    cfg = RockConfig.load()
    checks = []

    # Config Check
    if CONFIG_FILE.exists():
        checks.append(("Configuration File", "OK", f"Found at {CONFIG_FILE}"))
    else:
        checks.append(("Configuration File", "WARN", "Not initialized (run 'rock onboard')"))

    # Database Check
    try:
        db = DatabaseManager()
        tasks = db.list_tasks(limit=1)
        checks.append(("SQLite Persistence", "OK", f"Active at {DB_PATH}"))
    except Exception as e:
        checks.append(("SQLite Persistence", "FAIL", str(e)))

    # Workspace Check
    if WORKSPACE_DIR.exists():
        checks.append(("Workspace Sandbox", "OK", f"Active at {WORKSPACE_DIR}"))
    else:
        checks.append(("Workspace Sandbox", "WARN", "Directory will be created on start"))

    # Provider Key Check
    if cfg.providers:
        active_p = list(cfg.providers.keys())
        checks.append(("AI Providers Configured", "OK", ", ".join(active_p)))
    else:
        checks.append(("AI Providers Configured", "WARN", "No providers configured"))

    # Telegram Check
    if cfg.telegram_token:
        checks.append(("Telegram Mobile Bridge", "OK", "Bot token registered"))
    else:
        checks.append(("Telegram Mobile Bridge", "INFO", "Disabled (optional)"))

    table = Table(title="Diagnostics Summary", border_style="cyan")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Details", style="dim")

    for comp, status, detail in checks:
        color = "green" if status == "OK" else ("yellow" if status in ("WARN", "INFO") else "red")
        table.add_row(comp, f"[{color}]{status}[/{color}]", detail)

    console.print(table)

@daemon_app.command("start")
def daemon_start(port: Optional[int] = typer.Option(None, help="Port to listen on")):
    """Start 24/7 background gateway daemon and scheduler."""
    cfg = RockConfig.load()
    gateway = GatewayService(config=cfg)
    gateway.start(port=port)

@cron_app.command("list")
def cron_list():
    """List all scheduled recurring agent jobs."""
    db = DatabaseManager()
    jobs = db.list_cron_jobs()
    if not jobs:
        console.print("[dim]No recurring cron jobs configured.[/dim]")
        return

    table = Table(title="Autonomous Recurring Jobs", border_style="cyan")
    table.add_column("ID", style="bold cyan")
    table.add_column("Job Name", style="bold")
    table.add_column("Schedule", style="yellow")
    table.add_column("Goal", style="white")

    for j in jobs:
        table.add_row(str(j.id), j.name, j.cron_expression, j.goal)

    console.print(table)

@cron_app.command("add")
def cron_add(name: str, cron_expr: str, goal: str):
    """Register a new autonomous recurring job."""
    db = DatabaseManager()
    job = db.add_cron_job(name, cron_expr, goal)
    console.print(f"[bold green][OK] Cron job '{job.name}' registered successfully (Schedule: {job.cron_expression})[/bold green]")

if __name__ == "__main__":
    app()
