from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError(
        f"OPENAI_API_KEY was not loaded from {ENV_PATH}"
    )