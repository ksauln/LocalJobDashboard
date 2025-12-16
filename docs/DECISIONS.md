# Design Decisions

- **Local-first stack**: everything runs on your machine (Streamlit, SQLite, Chroma, Ollama) to avoid cloud lock-in or API keys.
- **No LangChain**: direct HTTP to Ollama keeps the dependency tree small and behavior transparent.
- **Chroma PersistentClient**: two stores (`data/vdb_jobs`, `data/vdb_resumes`) isolate embeddings and make it easy to wipe/reseed one side without touching the other.
- **SQLite for metadata/logs**: simple, file-based, and shippable; used for jobs/resumes tables plus run history shown in Settings.
- **Agents as reusable classes**: UI and CLI call the same agents (ingest/search/match) to prevent drift between interfaces.
- **Streamlit UI**: chosen for fast local prototyping and easy file upload/display; minimal custom components to keep setup simple.
- **Job sources kept explicit**: Remotive + scraper enabled by default; Greenhouse/Lever require user-supplied slugs; `JOB_SOURCES` env controls risk profile (e.g., `remotive` only to avoid scraping).
- **Optional LLM rerank**: hybrid vector + keyword scoring is the baseline; chat rerank can be toggled off to save time/compute.
- **Plain configuration**: `.env` holds everything; defaults favor local paths and common Ollama models so a noob can start quickly.
- **Testing/linting light but present**: pytest and ruff only; chosen to keep contribution barrier low while catching obvious issues.
