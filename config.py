import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env if present


# --------- Groq LLM Config ---------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_NAME: str = os.getenv(
    "GROQ_MODEL_NAME",
    "meta-llama/llama-4-scout-17b-16e-instruct"
)

if not GROQ_API_KEY:
    # You can remove this in prod; just for local debug
    print("[WARN] GROQ_API_KEY is not set. LLM calls will fail.")


# --------- Neo4j Config ---------
# For your sandbox you showed:
# bolt://54.157.21.239:7687
# --------- Neo4j Aura Cloud Config ---------
# --------- Neo4j Aura Cloud Config ---------
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://d7b24880.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD",
    "cYgzXxWJ3jI8C-7Niy8BhpIHI2PiZty5HWYfbGCC_g0"
)



if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    print("[WARN] Neo4j connection details are incomplete.")


# --------- App Config ---------
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "storage/uploads")
LOG_DIR: str = os.getenv("LOG_DIR", "storage/logs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
