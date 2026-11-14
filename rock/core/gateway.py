import asyncio
import threading
from typing import Optional
from fastapi import FastAPI
import uvicorn
from .config import RockConfig
from .database import DatabaseManager
from .scheduler import AutonomousScheduler
from ..agents.team import AgentTeam

try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

app = FastAPI(title="rock.ai 24/7 Gateway", version="0.1.0")

class GatewayService:
    """
    Central 24/7 background daemon handling REST healthchecks,
    autonomous cron scheduling, and Telegram mobile control.
    """

    def __init__(self, config: Optional[RockConfig] = None):
        self.config = config or RockConfig.load()
        self.db = DatabaseManager()
        self.team = AgentTeam(config=self.config)
        self.scheduler = AutonomousScheduler(db=self.db, team=self.team, config=self.config)

    def start(self, host: str = "0.0.0.0", port: Optional[int] = None):
        target_port = port or self.config.gateway_port

        # Start autonomous background scheduler
        self.scheduler.start()

        # Start Telegram mobile bridge if configured
        if self.config.telegram_token and TELEGRAM_AVAILABLE:
            threading.Thread(target=self._run_telegram_bot, daemon=True).start()

        # Define FastAPI endpoints
        @app.get("/health")
        def health():
            return {"status": "ok", "service": "rock.ai gateway", "version": "0.1.0"}

        @app.get("/api/tasks")
        def get_tasks():
            return self.db.list_tasks(limit=20)

        @app.get("/api/cron")
        def get_cron():
            return self.db.list_cron_jobs()

        print(f"[rock.ai] 24/7 Gateway running on http://{host}:{target_port}")
        uvicorn.run(app, host=host, port=target_port, log_level="warning")

    def _run_telegram_bot(self):
        """Runs the persistent Telegram bot in a dedicated background loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        application = ApplicationBuilder().token(self.config.telegram_token).build()

        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            welcome = (
                "🚀 *rock.ai Fleet Active 24/7*\n\n"
                "Your autonomous team is standing by:\n"
                "• *Captain*: Task planning & synthesis\n"
                "• *Researcher*: Web & data extraction\n"
                "• *Coder*: File & script builder\n"
                "• *Contrarian*: Logic audit & fact-checker\n\n"
                "Commands:\n"
                "/task <goal> - Run full 4-agent debate pipeline\n"
                "Or simply send a message (e.g. `@researcher find latest news`)."
            )
            await update.message.reply_text(welcome, parse_mode="Markdown")

        async def task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            goal = " ".join(context.args) if context.args else ""
            if not goal:
                await update.message.reply_text("Please provide a goal: `/task <your objective>`", parse_mode="Markdown")
                return

            await update.message.reply_text(f"⏳ *Captain has received goal:*\n_{goal}_\nStarting team debate...", parse_mode="Markdown")
            
            task_rec = self.db.create_task(goal)
            res = self.team.execute_goal(goal)
            self.db.update_task_completed(task_rec.id, res["final_answer"])

            await update.message.reply_text(f"✅ *Task Completed:*\n\n{res['final_answer']}", parse_mode="Markdown")

        async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_text = update.message.text
            res = self.team.group_chat(user_text)
            await update.message.reply_text(f"*{res['agent']}*: {res['reply']}", parse_mode="Markdown")

        application.add_handler(CommandHandler("start", start_cmd))
        application.add_handler(CommandHandler("task", task_cmd))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

        application.run_polling(close_loop=False)
