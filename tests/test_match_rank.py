from src.agents.match_rank import MatchRankAgent


def test_parse_llm_json_extracts_embedded_array():
    raw = """Based on the provided JSON data, here are insights:
    [{"job_id": "job-1", "score_0_to_100": 90, "strengths": ["python"], "gaps": [], "short_reason": "solid fit"}]
    Additional commentary."""

    parsed = MatchRankAgent._parse_llm_json(raw)

    assert parsed is not None
    assert parsed[0]["job_id"] == "job-1"
    assert parsed[0]["score_0_to_100"] == 90


def test_parse_llm_json_returns_none_for_missing_array():
    assert MatchRankAgent._parse_llm_json("Just a narrative with no JSON here.") is None


def test_llm_rerank_retries_when_first_response_not_json(monkeypatch):
    agent = MatchRankAgent(None, None)
    calls = {"count": 0}

    def fake_chat(_messages, model=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return "Here are some thoughts but no JSON."
        return '[{"job_id": "job-x", "score_0_to_100": 42, "strengths": [], "gaps": [], "short_reason": "ok"}]'

    monkeypatch.setattr("src.agents.match_rank.ollama_client.chat", fake_chat)
    result = agent._llm_rerank("resume text", [{"job_id": "job-x", "description": "desc"}])

    assert result["job-x"]["score_0_to_100"] == 42
    assert calls["count"] == 2
