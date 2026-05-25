"""Serve the LexAI web dashboard + API together."""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path

ROOT = Path(__file__).parent

if __name__ == "__main__":
    print("=" * 55)
    print("  LexAI — Starting API + Web Dashboard")
    print("=" * 55)
    print()
    print("  API  →  http://localhost:9000")
    print("  Docs →  http://localhost:9000/docs")
    print("  UI   →  http://localhost:9000")
    print()
    print("  Press Ctrl+C to stop.")
    print("=" * 55)

    time.sleep(1)
    webbrowser.open("http://localhost:9000")

    subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "uvicorn", "api.main:app",
         "--host", "0.0.0.0", "--port", "9000", "--reload"],
        cwd=str(ROOT),
    )
