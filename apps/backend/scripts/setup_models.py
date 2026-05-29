"""Pull all required Ollama models for NAP SLM architecture."""
import subprocess
import sys

MODELS = [
    "llama3.2:1b",   # Fast tier — simple lookups, translations
    "llama3.2:3b",   # Medium + Heavy tier — everything else
]


def pull_model(model: str):
    print(f"📥 Pulling {model}...")
    result = subprocess.run(
        ["ollama", "pull", model],
        capture_output=False,
    )
    if result.returncode == 0:
        print(f"   ✅ {model} ready")
    else:
        print(f"   ❌ Failed to pull {model}")


if __name__ == "__main__":
    print("🚀 NAP SLM Model Setup\n")
    print("This will download the models needed for fast inference.\n")

    for model in MODELS:
        pull_model(model)

    print("\n✅ All models ready. Run: python main.py")
