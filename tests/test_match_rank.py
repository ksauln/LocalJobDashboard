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


def test_parse_llm_json_wraps_object_into_list():
    raw = '{"job_id": "job-obj", "score_0_to_100": 75, "strengths": [], "gaps": [], "short_reason": "ok"}'

    parsed = MatchRankAgent._parse_llm_json(raw)

    assert parsed is not None
    assert parsed[0]["job_id"] == "job-obj"


def test_llm_rerank_retries_when_first_response_not_json(monkeypatch):
    agent = MatchRankAgent(None, None)
    calls = {"count": 0}

    def fake_chat(_messages, model=None, format=None):
        assert format == "json"
        calls["count"] += 1
        if calls["count"] == 1:
            return "Here are some thoughts but no JSON."
        return '[{"job_id": "job-x", "score_0_to_100": 42, "strengths": [], "gaps": [], "short_reason": "ok"}]'

    monkeypatch.setattr("src.agents.match_rank.chat", fake_chat)
    result = agent._llm_rerank("resume text", [{"job_id": "job-x", "description": "desc"}])

    assert result["job-x"]["score_0_to_100"] == 42
    assert calls["count"] == 2


def test_llm_rerank_third_prompt_used_if_needed(monkeypatch):
    agent = MatchRankAgent(None, None)
    calls = {"count": 0}

    def fake_chat(_messages, model=None, format=None):
        assert format == "json"
        calls["count"] += 1
        if calls["count"] < 3:
            return "Analysis without JSON"
        return '[{"job_id": "job-y", "score_0_to_100": 99, "strengths": [], "gaps": [], "short_reason": "great"}]'

    monkeypatch.setattr("src.agents.match_rank.chat", fake_chat)
    result = agent._llm_rerank("resume text", [{"job_id": "job-y", "description": "desc"}])

    assert result["job-y"]["score_0_to_100"] == 99
    assert calls["count"] == 3


def test_parse_llm_json_accepts_structured_output():
    raw = {"job_id": "job-z", "score_0_to_100": 80, "strengths": ["py"], "gaps": [], "short_reason": "good"}

    parsed = MatchRankAgent._parse_llm_json(raw)

    assert parsed == [raw]


def test_llm_rerank_handles_non_string_chat_output(monkeypatch):
    agent = MatchRankAgent(None, None)

    def fake_chat(_messages, model=None, format=None):
        assert format == "json"
        return [{"job_id": "job-a", "score_0_to_100": 88, "strengths": [], "gaps": [], "short_reason": "solid"}]

    monkeypatch.setattr("src.agents.match_rank.chat", fake_chat)

    result = agent._llm_rerank("resume text", [{"job_id": "job-a", "description": "desc"}])

    assert result["job-a"]["score_0_to_100"] == 88


def test_llm_rerank_fills_missing_with_hybrid(monkeypatch):
    agent = MatchRankAgent(None, None)

    def fake_chat(_messages, model=None, format=None):
        assert format == "json"
        # Always omit job-miss to force fallback
        return '[{"job_id": "job-keep", "score_0_to_100": 70, "strengths": [], "gaps": [], "short_reason": "ok"}]'

    monkeypatch.setattr("src.agents.match_rank.chat", fake_chat)

    jobs = [
        {"job_id": "job-keep", "description": "desc1", "hybrid_score": 70},
        {"job_id": "job-miss", "description": "desc2", "hybrid_score": 55},
    ]

    result = agent._llm_rerank("resume text", jobs)

    assert result["job-keep"]["score_0_to_100"] == 70
    assert result["job-miss"]["score_0_to_100"] == 55
    assert "Filled from hybrid score" in result["job-miss"]["short_reason"]
