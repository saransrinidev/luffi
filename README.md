![Luffi](public/image.png)

# Luffi — Local AI Desktop Assistant

A Windows desktop AI assistant that captures highlighted text via a global hotkey and explains it using a local Ollama LLM, displayed in a futuristic floating popup centered on screen.

## Architecture

```
apps/
└── backend/       (Python + FastAPI + tkinter popup UI)
```

## Flow

1. User highlights text anywhere in Windows
2. Presses `Ctrl+;`
3. Backend detects hotkey → simulates Ctrl+C → reads clipboard
4. Sends text to local Ollama API
5. Futuristic dark popup appears centered on screen with the explanation

## Quick Start

```bash
cd apps/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Requirements

- Python 3.11+
- Ollama running locally (http://localhost:11434)
- Run terminal as Administrator (for global hotkeys)

## Models Supported

- llama3.2:1b (fast tier)
- llama3.2:3b (medium tier)
