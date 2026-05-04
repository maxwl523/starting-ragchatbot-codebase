import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional

from test_constants import (
    MOCK_ANSWER,
    MOCK_COURSES,
    MOCK_SESSION_ID,
    MOCK_SOURCE_LABEL,
    MOCK_SOURCE_URL,
)


# ---------------------------------------------------------------------------
# Pydantic models (mirrors app.py — decoupled from static-file mounts and
# live infrastructure so tests run without a ChromaDB or Anthropic key)
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class SourceItem(BaseModel):
    label: str
    url: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    session_id: str


class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


# ---------------------------------------------------------------------------
# Fixture: mock RAGSystem
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_rag_system():
    rag = MagicMock()
    rag.session_manager.create_session.return_value = MOCK_SESSION_ID
    rag.query.return_value = (
        MOCK_ANSWER,
        [{"label": MOCK_SOURCE_LABEL, "url": MOCK_SOURCE_URL}],
    )
    rag.get_course_analytics.return_value = {
        "total_courses": len(MOCK_COURSES),
        "course_titles": MOCK_COURSES,
    }
    return rag


# ---------------------------------------------------------------------------
# Fixture: isolated test FastAPI app (no static files, no startup ingestion)
# ---------------------------------------------------------------------------

@pytest.fixture
def test_app(mock_rag_system):
    app = FastAPI(title="Test RAG App")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()
            answer, sources = mock_rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/session/{session_id}")
    async def delete_session(session_id: str):
        mock_rag_system.session_manager.clear_session(session_id)
        return {"status": "cleared"}

    return app


# ---------------------------------------------------------------------------
# Fixture: synchronous TestClient
# ---------------------------------------------------------------------------

@pytest.fixture
def client(test_app):
    return TestClient(test_app)
