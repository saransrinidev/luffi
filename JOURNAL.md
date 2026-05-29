# NAP — Project Journal

## What is NAP?

NAP (short name, clean name) is a **local AI desktop assistant for Windows**. You highlight any text anywhere on your screen, press a hotkey, and a futuristic popup appears with an AI-generated explanation — all running locally, no cloud, no API keys, no internet needed.

---

## How It Started

The idea came from a simple workflow pain point:

> "I'm reading something, I see a term or code snippet I don't understand, I want an instant explanation without switching apps, opening a browser, or copy-pasting into ChatGPT."

The goal was to build something that:
- Works **system-wide** (any app, any window)
- Runs **100% locally** (Ollama + local LLMs)
- Feels **instant and native** (global hotkey + popup)
- Stays **minimal** (no bloated Electron app for now)

---

## Architecture Decisions

### Started with (original plan):
```
Frontend: Electron + Next.js + TailwindCSS + Shadcn/ui
Backend:  Python + FastAPI
```

### Simplified to (current):
```
Backend only: Python + FastAPI + tkinter popup
```

**Why the change:** Electron is overkill for a popup that shows text. Python's built-in tkinter handles the UI just fine — zero extra dependencies, instant startup, and the futuristic look is achieved with custom styling.

---

## How It Works (Technical Flow)

```
User highlights text anywhere in Windows
        │
        ▼
Presses Ctrl+;
        │
        ▼
keyboard package detects global hotkey
        │
        ▼
pyautogui simulates Ctrl+C
        │
        ▼
pyperclip reads clipboard content
        │
        ▼
httpx sends text to FastAPI /explain endpoint
        │
        ▼
FastAPI calls Ollama API (localhost:11434)
        │
        ▼
Ollama runs local LLM (llama3.2:3b)
        │
        ▼
Response comes back
        │
        ▼
tkinter popup appears CENTER of screen
(dark, transparent, futuristic, frameless)
        │
        ▼
User reads explanation, presses Escape to close
```

---

## Project Structure

```
nap/
├── apps/
│   └── backend/
│       ├── main.py              → FastAPI app + hotkey thread startup
│       ├── config.py            → Settings via pydantic-settings + .env
│       ├── routes.py            → POST /explain, GET /health
│       ├── requirements.txt     → All Python dependencies
│       ├── .env                 → Environment config
│       └── services/
│           ├── hotkey_service.py     → Global hotkey listener (Ctrl+;)
│           ├── clipboard_service.py  → Ctrl+C simulation + clipboard read
│           ├── llm_service.py        → Ollama API communication
│           └── popup_service.py      → Futuristic tkinter popup UI
├── .gitignore
├── README.md
└── JOURNAL.md
```

---

## Key Components

### 1. Hotkey Service (`hotkey_service.py`)
- Registers `Ctrl+;` as a global system-wide hotkey
- Runs in a daemon thread so it doesn't block FastAPI
- Plays audio beeps for feedback (startup, trigger, success, error)
- Coordinates the full flow: capture → LLM → popup

### 2. Clipboard Service (`clipboard_service.py`)
- Saves current clipboard before capturing
- Simulates Ctrl+C via pyautogui
- Waits briefly for clipboard to update
- Returns the captured text (or None if nothing selected)

### 3. LLM Service (`llm_service.py`)
- Async HTTP calls to Ollama's `/api/generate` endpoint
- Configurable model (default: llama3.2:3b)
- Prompt engineered for clear, concise explanations
- Supports model switching via API param or .env

### 4. Popup Service (`popup_service.py`)
- Frameless, always-on-top tkinter window
- Centered on screen
- 92% opacity (semi-transparent)
- Dark theme: near-black background (#0d0d1a) with cyan accents (#00d4ff)
- Scrollable text area for long responses
- Close with Escape key or ✕ button
- Runs in its own thread to not block anything

---

## Config (.env)

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
HOTKEY=ctrl+;
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=info
```

---

## Dependencies

| Package          | Purpose                        |
|------------------|--------------------------------|
| fastapi          | REST API framework             |
| uvicorn          | ASGI server                    |
| keyboard         | Global hotkey detection         |
| pyautogui        | Ctrl+C simulation              |
| pyperclip        | Clipboard read/write           |
| httpx            | Async HTTP client for Ollama   |
| pydantic-settings| Config management from .env    |

---

## How to Run

```bash
cd apps/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Prerequisites:**
- Ollama running (`ollama serve` or desktop app)
- A model pulled (`ollama pull llama3.2:3b`)
- Terminal running as Administrator (for global hotkeys)

---

## Audio Feedback

| Sound            | Meaning                        |
|------------------|--------------------------------|
| 1000Hz beep      | Backend started, ready         |
| 1500Hz short     | Hotkey detected                |
| 2000Hz short     | Explanation received (success) |
| 400Hz low        | Error or nothing captured      |

---

## Future Possibilities

- [ ] OCR (capture text from images/screenshots)
- [ ] Voice commands
- [ ] Screen understanding (what's on screen)
- [ ] Agent mode (take actions, not just explain)
- [ ] Cursor control
- [ ] Multiple prompt modes (explain, translate, summarize, code review)
- [ ] History of past queries
- [ ] Electron/web UI upgrade (when needed)
- [ ] Streaming responses in popup
- [ ] Custom prompt templates

---

## Timeline

| Step | What happened |
|------|---------------|
| 1    | Planned full Electron + Next.js + FastAPI architecture |
| 2    | Scaffolded both frontend and backend |
| 3    | Realized Electron is overkill for current needs |
| 4    | Built futuristic tkinter popup instead |
| 5    | Removed all frontend code |
| 6    | Final: Pure Python backend with native popup UI |

---

*Built locally. Runs locally. No cloud. No telemetry. Just you and your local LLM.*
