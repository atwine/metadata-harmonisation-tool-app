"""
Run from the project root:  python run_backend.py
This keeps input/, results/, logs/ relative to the project root.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host=os.environ.get("MHT_BIND_ADDRESS", "127.0.0.1"), port=8000, reload=True, reload_dirs=["backend"])
