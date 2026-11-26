import asyncio
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
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
_default_service: Optional["GatewayService"] = None

def get_gateway_service() -> "GatewayService":
    global _default_service
    if _default_service is None:
        _default_service = GatewayService()
    return _default_service

# Request schemas
class ChatRequest(BaseModel):
    message: str

class TaskRequest(BaseModel):
    goal: str

class CreateAgentRequest(BaseModel):
    name: str
    role: str
    system_prompt: str
    model: Optional[str] = None

class GatewayService:
    """
    Central 24/7 background daemon handling REST healthchecks,
    autonomous cron scheduling, visual web UI, and Telegram mobile control.
    """

    def __init__(self, config: Optional[RockConfig] = None):
        self.config = config or RockConfig.load()
        self.db = DatabaseManager()
        self.team = AgentTeam(config=self.config, db=self.db)
        self.scheduler = AutonomousScheduler(db=self.db, team=self.team, config=self.config)
        self.subscribers: List[asyncio.Queue] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Wire event listener from team to SSE subscribers
        self.team.on_event = self._broadcast_event_sync

    def _broadcast_event_sync(self, event: Dict[str, Any]):
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast_event(event), self._loop)

    async def _broadcast_event(self, event: Dict[str, Any]):
        dead = []
        for q in self.subscribers:
            try:
                await q.put(event)
            except Exception:
                dead.append(q)
        for d in dead:
            if d in self.subscribers:
                self.subscribers.remove(d)

    def start(self, host: str = "0.0.0.0", port: Optional[int] = None):
        global _default_service
        _default_service = self
        target_port = port or self.config.gateway_port
        self.scheduler.start()

        if self.config.telegram_token and TELEGRAM_AVAILABLE:
            threading.Thread(target=self._run_telegram_bot, daemon=True).start()

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

# Module-level Route Registrations on app
template_path = Path(__file__).parent.parent / "ui" / "templates" / "index.html"

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<html><body><h1>rock.ai Dashboard Template Not Found</h1></body></html>"

@app.get("/health")
def health():
    return {"status": "ok", "service": "rock.ai gateway", "version": "0.1.0"}

@app.get("/api/agents")
def get_agents():
    service = get_gateway_service()
    return service.team.list_roster()

@app.post("/api/agents")
def create_agent(req: CreateAgentRequest):
    service = get_gateway_service()
    try:
        rec = service.team.register_custom_agent(
            name=req.name,
            role=req.role,
            system_prompt=req.system_prompt,
            model=req.model,
            created_by="user"
        )
        return {"status": "created", "agent": rec.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/agents/{name}")
def delete_agent(name: str):
    service = get_gateway_service()
    success = service.team.delete_custom_agent(name)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete agent (built-in or not found)")
    return {"status": "deleted", "name": name}

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    service = get_gateway_service()
    try:
        res = service.team.group_chat(req.message)
        return res
    except Exception as e:
        return {"agent": "System", "reply": f"⚠️ Error: {str(e)}"}

@app.post("/api/task")
def task_endpoint(req: TaskRequest):
    service = get_gateway_service()
    try:
        task_rec = service.db.create_task(req.goal)
        res = service.team.execute_goal(req.goal)
        service.db.update_task_completed(task_rec.id, res["final_answer"])
        return res
    except Exception as e:
        return {
            "goal": req.goal,
            "final_answer": f"⚠️ Task Failed: {str(e)}",
            "debate": {}
        }

@app.get("/api/tasks")
def get_tasks():
    service = get_gateway_service()
    return service.db.list_tasks(limit=20)

@app.get("/api/cron")
def get_cron():
    service = get_gateway_service()
    return service.db.list_cron_jobs()

@app.get("/api/events/stream")
async def event_stream():
    service = get_gateway_service()
    queue: asyncio.Queue = asyncio.Queue()
    service.subscribers.append(queue)
    service._loop = asyncio.get_event_loop()

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            if queue in service.subscribers:
                service.subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
