from src.tools.scoring import distance_to_score, keyword_overlap, hybrid_score


def test_distance_to_score_bounds():
    assert 0 <= distance_to_score(0.5) <= 100
    assert distance_to_score(-1) == 100


def test_keyword_overlap_range():
    score = keyword_overlap("python data", "python engineer")
    assert 0 <= score <= 100


def test_hybrid_score():
    assert hybrid_score(80, 50) == 71
