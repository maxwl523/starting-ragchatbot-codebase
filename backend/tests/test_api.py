"""API endpoint tests for the RAG chatbot backend."""
from test_constants import (
    MOCK_ANSWER,
    MOCK_COURSES,
    MOCK_SESSION_ID,
    MOCK_SOURCE_LABEL,
)


# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------

class TestQueryEndpoint:
    def test_query_creates_session_when_none_provided(self, client):
        response = client.post("/api/query", json={"query": "What is Python?"})
        assert response.status_code == 200
        assert response.json()["session_id"] == MOCK_SESSION_ID

    def test_query_uses_provided_session_id(self, client):
        response = client.post(
            "/api/query",
            json={"query": "Tell me about loops", "session_id": "existing_session"},
        )
        assert response.status_code == 200
        assert response.json()["session_id"] == "existing_session"

    def test_query_returns_answer(self, client):
        response = client.post("/api/query", json={"query": "What is Python?"})
        assert response.status_code == 200
        assert response.json()["answer"] == MOCK_ANSWER

    def test_query_returns_sources(self, client):
        response = client.post("/api/query", json={"query": "What is Python?"})
        assert response.status_code == 200
        sources = response.json()["sources"]
        assert isinstance(sources, list)
        assert len(sources) == 1
        assert sources[0]["label"] == MOCK_SOURCE_LABEL

    def test_query_response_has_required_fields(self, client):
        data = client.post("/api/query", json={"query": "What is Python?"}).json()
        assert {"answer", "sources", "session_id"}.issubset(data.keys())

    def test_query_missing_query_field_returns_422(self, client):
        response = client.post("/api/query", json={})
        assert response.status_code == 422

    def test_query_propagates_rag_error_as_500(self, client, mock_rag_system):
        mock_rag_system.query.side_effect = RuntimeError("DB unavailable")
        response = client.post("/api/query", json={"query": "boom"})
        assert response.status_code == 500
        assert "DB unavailable" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------

class TestCoursesEndpoint:
    def test_courses_returns_200(self, client):
        assert client.get("/api/courses").status_code == 200

    def test_courses_total_count(self, client):
        assert client.get("/api/courses").json()["total_courses"] == len(MOCK_COURSES)

    def test_courses_titles_list(self, client):
        assert client.get("/api/courses").json()["course_titles"] == MOCK_COURSES

    def test_courses_response_has_required_fields(self, client):
        data = client.get("/api/courses").json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["course_titles"], list)

    def test_courses_propagates_error_as_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = RuntimeError("store down")
        response = client.get("/api/courses")
        assert response.status_code == 500
        assert "store down" in response.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /api/session/{session_id}
# ---------------------------------------------------------------------------

class TestSessionEndpoint:
    def test_delete_session_returns_200(self, client):
        assert client.delete("/api/session/session_1").status_code == 200

    def test_delete_session_returns_cleared_status(self, client):
        assert client.delete("/api/session/session_1").json() == {"status": "cleared"}

    def test_delete_session_calls_clear_session(self, client, mock_rag_system):
        client.delete("/api/session/my_session")
        mock_rag_system.session_manager.clear_session.assert_called_once_with("my_session")
