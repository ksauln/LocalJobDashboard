import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
SQLITE_PATH = os.getenv("SQLITE_PATH", "./data/app.db")
VDB_JOBS_DIR = os.getenv("VDB_JOBS_DIR", "./data/vdb_jobs")
VDB_RESUMES_DIR = os.getenv("VDB_RESUMES_DIR", "./data/vdb_resumes")
JOB_SOURCES = [s.strip() for s in os.getenv("JOB_SOURCES", "remotive,scraper").split(",") if s.strip()]
GREENHOUSE_BOARDS = [b.strip() for b in os.getenv("GREENHOUSE_BOARDS", "").split(",") if b.strip()]
LEVER_COMPANIES = [c.strip() for c in os.getenv("LEVER_COMPANIES", "").split(",") if c.strip()]
REMOTIVE_CATEGORY = os.getenv("REMOTIVE_CATEGORY", "")
