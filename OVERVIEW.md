![Luffi](public/image.png)

# Luffi — Complete Overview

A fully local Windows AI assistant. No cloud, no API keys, no internet. Everything runs on your machine via Ollama.

---

## Two Core Capabilities

### 1. Text Intelligence (highlight → hotkey → answer)

Highlight any text anywhere in Windows, press a hotkey, get an AI response in a CMD-style popup.

| Hotkey | Mode |
|--------|------|
| `Ctrl+;` | Explain |
| `Ctrl+'` | Translate |
| `Ctrl+/` | Summarize |
| `Ctrl+Shift+/` | Code Review |
| `Ctrl+Shift+'` | ELI5 (explain simply) |
| `Ctrl+Shift+;` | Ask box (free input + agent) |

**How it works:** hotkey → simulate Ctrl+C → read clipboard → send to Ollama → show result in popup.

### 2. Desktop Automation Agent (controls your computer)

Type a command in the Ask box, and Luffi physically moves your cursor and types — like a human.

---

## How the Agent Works — The Layered Architecture

The key design principle: **keep the small model's job tiny**. Most work is done by code, not the LLM.

```
You type: "open firefox and search youtube"
    │
    ▼
┌─ Layer 1: INTENT ────────────────────────────┐
│ Regex extracts: {app:firefox, goal:youtube,  │
│                  type:browser_search}         │
│ → Instant, no LLM for known patterns          │
└───────────────────────────────────────────────┘
    │
    ▼
┌─ Layer 2: TEMPLATE ENGINE ───────────────────┐
│ Matches browser_search → fixed step sequence: │
│   launch → ctrl+L → type → enter → done       │
│ → If confident (95%), SKIP LLM entirely        │
└───────────────────────────────────────────────┘
    │
    ▼ (only if no template matches)
┌─ Layer 3: UI RETRIEVAL ──────────────────────┐
│ Windows UIAutomation reads every element:     │
│   buttons, fields, names, coordinates         │
└───────────────────────────────────────────────┘
    │
    ▼
┌─ Layer 4: CANDIDATE FILTERING (code) ────────┐
│ Scores elements by heuristics:                │
│   +5 control type match, +5 keyword match,    │
│   +8 address bar match, etc.                  │
│ → Returns ONLY top 3-5 candidates             │
└───────────────────────────────────────────────┘
    │
    ▼
┌─ Layer 5: DECISION (LLM) ────────────────────┐
│ LLM sees ONLY 3-5 options + goal              │
│ Returns just a number: "1"                    │
│ → Tiny task even a 1B model handles           │
└───────────────────────────────────────────────┘
    │
    ▼
┌─ Layer 6: EXECUTION ─────────────────────────┐
│ Human-like cursor (bezier curves, jitter)    │
│ Human-like typing (variable speed, pauses)   │
│ Clicks, types, hotkeys, launches apps        │
└───────────────────────────────────────────────┘
    │
    ▼
┌─ Layer 7: VERIFICATION ──────────────────────┐
│ Did focus change? Window change? Retry if not │
└───────────────────────────────────────────────┘
```

**Why this matters:** A naive agent dumps the whole screen + task on the LLM and hopes a 3B model figures it out (it can't). Luffi does 90% with code and gives the LLM a multiple-choice question instead of an essay.

---

## What It Can Do Right Now

### Browser
| Command | Action |
|---------|--------|
| `open firefox and search youtube` | Opens Firefox, searches |
| `open chrome and search python tutorials` | Opens Chrome, searches |
| `open edge and go to github.com` | Opens Edge, navigates |
| `search cute cats` | Opens browser, searches |
| `google weather today` | Opens browser, searches |
| `go to youtube.com` | Navigates to URL |
| `visit github.com` | Navigates |

### Calculator (any math expression)
| Command | Action |
|---------|--------|
| `open calculator and calculate 2 + 2` | Opens calc, clicks buttons visually |
| `calculate 25 + 17` | Computes |
| `compute 100 - 45` | Computes |
| `calculate 8 * 9` | Computes |
| `calculate 144 / 12` | Computes |

### App Launch
| Command | Action |
|---------|--------|
| `open notepad` | Launches Notepad |
| `open firefox` / `launch chrome` | Launches browser |
| `open explorer` | Launches File Explorer |
| `open cmd` / `open terminal` | Launches terminal |
| `open code` / `open vscode` | Launches VS Code |
| `open paint` | Launches Paint |

### File Explorer
| Command | Action |
|---------|--------|
| `open folder C:\Users` | Navigates to path |
| `go to directory D:\Projects` | Navigates |

### Tabs & Typing
| Command | Action |
|---------|--------|
| `new tab` | Ctrl+T |
| `close tab` | Ctrl+W |
| `type hello world` | Types text at cursor |

---

## The SLM Speed Stack (text mode)

Responses are sped up via:

1. **Cache** — repeated questions answered instantly (0ms)
2. **Compressor** — strips whitespace/comments before sending
3. **Router** — simple queries → 1B model, complex → 3B model
4. **Tuned params** — low temperature, small context, limited output

---

## Models Used

| Model | Role |
|-------|------|
| `llama3.2:1b` | Fast — intent classification, simple lookups |
| `llama3.2:3b` | Medium — explanations, summaries |
| `qwen2.5:7b` | Agent — element decisions (best at structured output) |

---

## Extra Features

- **History** — every query saved to SQLite
- **System tray** — icon with model switcher
- **Status bar** — small bottom-left progress bar during agent runs (doesn't block screen capture)
- **Human-like motion** — cursor glides in curves, types at variable speed with natural pauses
- **Auto-start** — script to launch Luffi on Windows boot
- **OCR** (optional) — screenshot → text extraction
- **Voice** (optional) — Whisper transcription
- **Clipboard watcher** — auto-explain on copy
- **Context detection** — knows which app is focused

---

## Architecture

```
apps/backend/
├── agent/              ← The 7-layer automation pipeline
│   ├── intent_layer.py       (Layer 1: extract intent)
│   ├── template_engine.py    (Layer 2: deterministic actions)
│   ├── ui_layer.py           (Layer 3+4: UI scan + scoring)
│   ├── decision_layer.py     (Layer 5: LLM picks candidate)
│   ├── execution_layer.py    (Layer 6: PyAutoGUI execution)
│   ├── verification_layer.py (Layer 7: confirm success)
│   └── orchestrator.py       (connects all layers)
├── services/           ← 20+ supporting services
│   ├── desktop_service.py    (Windows UIAutomation reader)
│   ├── mouse_service.py      (human-like cursor + typing)
│   ├── hotkey_service.py     (global hotkey listener)
│   ├── popup_service.py      (CMD-style result popup)
│   ├── status_bar_service.py (bottom-left progress bar)
│   ├── llm_service.py        (Ollama calls + SLM stack)
│   └── ... (cache, router, history, tray, etc.)
├── main.py             ← FastAPI + hotkeys + tray
├── config.py
└── prompts.json
```

---

## Tech Stack

- **Backend:** Python + FastAPI
- **LLM:** Ollama (local)
- **Perception:** Windows UIAutomation API
- **Control:** PyAutoGUI + keyboard
- **UI:** tkinter (popup + status bar)

---

## The Big Picture

Luffi started as a text-explainer and grew into a local desktop agent. The breakthrough was the layered architecture — making a small 3B model reliable by shrinking its decisions to multiple-choice picks while code handles perception, filtering, and execution.

*Built locally. Runs locally. No cloud. No telemetry.*
