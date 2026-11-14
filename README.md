# rock.ai 🪨

> **Autonomous 24/7 Persistent Multi-Agent Fleet**  
> An open-source, model-agnostic multi-agent coworker framework with interactive terminal onboarding and continuous background execution.

---

## Highlights

- **4-Agent Collaborative Fleet**: Includes Captain (Lead), Researcher (Web/Data), Coder (Sandbox Executor), and Contrarian (Auditor/Critic).
- **24/7 Always-On Operation**: Runs continuously in the background via local daemon or zero-cost cloud deployment (Oracle Cloud Always Free / Docker) even when your PC is turned off.
- **Universal Model Router**: Bring your own keys for OpenAI, Anthropic Claude, Google Gemini, DeepSeek, xAI Grok, Ollama, OpenRouter, or custom OpenAI-compatible endpoints.
- **Interactive Terminal Setup**: One-command onboarding wizard (`rock onboard`) for fast, guided configuration.
- **Mobile Remote Bridge**: Integrated Telegram bot gateway to assign tasks, chat with agents, and receive alerts from your phone.
- **Sandboxed Tool Execution**: Safe workspace filesystem and script execution with path protection and safety filters.

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │          Interfaces                  │
                      │  • Terminal CLI (rock chat)          │
                      │  • Telegram Bot Gateway              │
                      │  • REST API & Healthcheck            │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │       rock.ai Gateway Daemon         │
                      │  • Task Queue & Cron Scheduler       │
                      │  • Workspace Security Sandbox        │
                      └──────────────────┬───────────────────┘
                                         │
                      ┌──────────────────┴───────────────────┐
                      ▼                                      ▼
          ┌───────────────────────┐              ┌───────────────────────┐
          │   Multi-Agent Team    │              │  Universal Model Hub  │
          │  • Captain            │              │  • OpenAI  • Claude   │
          │  • Researcher         │◄────────────►│  • Gemini  • DeepSeek │
          │  • Coder              │              │  • Grok    • Ollama   │
          │  • Contrarian         │              │  • OpenRouter         │
          └───────────┬───────────┘              └───────────────────────┘
                      │
                      ▼
          ┌──────────────────────────────────────┐
          │      Persistent Storage & Memory     │
          │  • SQLite DB (~/.rock/rock.db)       │
          │  • Sandboxed Workspace (~/.rock/)    │
          └──────────────────────────────────────┘
```

---

## Quickstart

### 1. Installation

#### Via Script (Linux / macOS):
```bash
curl -fsSL https://raw.githubusercontent.com/airvalona/rock-ai/main/install.sh | bash
```

#### Via Script (Windows PowerShell):
```powershell
irm https://raw.githubusercontent.com/airvalona/rock-ai/main/install.ps1 | iex
```

#### Via Pip:
```bash
pip install -e .
```

---

### 2. Interactive Terminal Setup

Run the onboarding wizard to configure providers, API keys, and workspace settings:

```bash
rock onboard
```

---

### 3. Usage Commands

| Command | Description |
| :--- | :--- |
| `rock onboard` | Run the interactive setup wizard |
| `rock chat` | Start interactive terminal chat with the agent team |
| `rock task "<objective>"` | Run full 4-agent debate pipeline on a specific goal |
| `rock team` | Inspect the agent roster and model assignments |
| `rock daemon start` | Launch the 24/7 background gateway daemon |
| `rock cron list` | View scheduled recurring agent jobs |
| `rock cron add <name> <expr> <goal>` | Register an autonomous cron job |
| `rock doctor` | Run system and configuration diagnostics |

---

### 4. 24/7 Zero-Cost Cloud Deployment (Docker)

To run rock.ai continuously without keeping your computer on:

```bash
docker compose up -d
```

The gateway daemon will start, load your persistent cron jobs, and listen for incoming tasks and Telegram messages 24/7.

---

## License

MIT License. Free and open source for everyone.
