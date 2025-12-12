# Design Decisions

- **No LangChain**: direct HTTP calls to Ollama for embeddings and chat keep dependencies light.
- **Chroma PersistentClient**: two separate stores (`data/vdb_jobs`, `data/vdb_resumes`) isolate embeddings and allow local persistence.
- **SQLite Metadata**: simple relational store for jobs, resumes, and run logs keeps the stack local-first.
- **Agents as Classes**: ResumeIngestAgent, JobScoutAgent, and MatchRankAgent encapsulate workflows without external orchestration.
- **Safe Sources**: Greenhouse, Lever, Remotive public APIs plus a Dummy source avoid scraping and ease setup.
