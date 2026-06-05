from src.services.crisis_detector import build_crisis_metadata, detect_crisis


def test_detect_crisis_keywords():
    assert detect_crisis("I feel suicidal") is True
    assert detect_crisis("thinking about self-harm") is True


def test_detect_crisis_negative():
    assert detect_crisis("I feel anxious about work") is False


def test_crisis_metadata_includes_helplines():
    metadata = build_crisis_metadata()
    assert metadata.crisis_detected is True
    assert metadata.region == "US"
    assert any(h.phone == "988" for h in metadata.helplines)
