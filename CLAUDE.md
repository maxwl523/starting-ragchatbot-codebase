# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Always use `uv` to manage dependencies and run Python files — never use `pip` or `python` directly.

**Install dependencies:**
```bash
uv sync
```

**Add a dependency:**
```bash
uv add <package>
```

**Run a Python file:**
```bash
uv run <file.py>
```

**Run the application:**
```bash
./run.sh
# or manually:
cd backend && uv run uvicorn app:app --reload --port 8000
```

The app runs at `http://localhost:8000` and API docs at `http://localhost:8000/docs`.

**Environment setup:**
Create a `.env` file in the root with:
```
ANTHROPIC_API_KEY=your_key_here
```

## Architecture

This is a full-stack RAG (Retrieval-Augmented Generation) chatbot for querying course materials.

**Request flow:**
1. Frontend (static HTML/JS in `frontend/`) sends POST to `/api/query`
2. `backend/app.py` (FastAPI) routes the request to `RAGSystem.query()`
3. `RAGSystem` passes the query to `AIGenerator`, which calls Claude with a `search_course_content` tool available
4. If Claude decides to search, `ToolManager` dispatches to `CourseSearchTool`, which queries `VectorStore` (ChromaDB)
5. Search results are injected back into the conversation and Claude generates a final answer
6. Sources from the search are tracked and returned alongside the answer

**Key backend modules:**
- `backend/rag_system.py` — Top-level orchestrator; wires all components together
- `backend/ai_generator.py` — Anthropic API client; handles the tool-use loop (initial call → tool execution → follow-up call)
- `backend/vector_store.py` — ChromaDB wrapper with two collections: `course_catalog` (course metadata) and `course_content` (chunked lesson text)
- `backend/search_tools.py` — `CourseSearchTool` (the single Claude tool) + `ToolManager` registry
- `backend/document_processor.py` — Parses `.txt` course files into `Course`/`Lesson`/`CourseChunk` models and splits text into overlapping chunks
- `backend/session_manager.py` — In-memory conversation history keyed by session ID
- `backend/config.py` — Single `Config` dataclass; reads from `.env`

**Course document format** (files in `docs/`):
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: <lesson title>
Lesson Link: <url>
<lesson content...>

Lesson 1: <lesson title>
...
```

On startup, `app.py` automatically ingests all `.pdf`, `.docx`, and `.txt` files from `../docs/`. Already-indexed courses are skipped (deduped by title).

**ChromaDB** persists to `backend/chroma_db/` (gitignored). To reindex from scratch, call `VectorStore.clear_all_data()` or delete that directory.

**Model:** `claude-sonnet-4-20250514` with `temperature=0`, `max_tokens=800`. One tool use per query (enforced by system prompt instruction, not API-level).