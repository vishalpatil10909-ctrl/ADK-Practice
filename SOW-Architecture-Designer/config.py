import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the package-local .env file.
# Use override=True so the configured .env value wins over any existing process env.
base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env", override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
