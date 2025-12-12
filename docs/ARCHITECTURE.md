# Architecture

## Overview
The Local Agentic Job Dashboard couples a Streamlit UI with lightweight agents for resume ingestion, job scouting, and matching/reranking. SQLite stores metadata and logs, while two Chroma persistent vector databases hold embeddings for resumes and jobs. Ollama provides embeddings and optional chat-based reranking.

## Diagram
```mermaid
flowchart LR
UI[Streamlit UI] --> A1[ResumeIngestAgent]
UI --> A2[JobScoutAgent]
UI --> A3[MatchRankAgent]
A1 --> RDB[(SQLite)]
A2 --> RDB
A3 --> RDB
A1 --> RVDB[(Chroma Resumes)]
A2 --> JVDB[(Chroma Jobs)]
A3 --> RVDB
A3 --> JVDB
A1 --> O[Ollama Embeddings]
A2 --> O
A3 --> O2[Ollama Chat Rerank]
```
