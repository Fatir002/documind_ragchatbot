"""Tests for app/qa/history.py: conversation memory bounds and formatting."""

from app.qa.history import ConversationHistory


def test_empty_history_renders_as_empty_string() -> None:
    history = ConversationHistory()
    assert history.as_text() == ""


def test_added_turns_appear_in_rendered_text() -> None:
    history = ConversationHistory()
    history.add("What is X?", "X is Y.")
    text = history.as_text()
    assert "What is X?" in text
    assert "X is Y." in text


def test_history_is_capped_at_max_turns() -> None:
    history = ConversationHistory(max_turns=3)
    for i in range(5):
        history.add(f"question {i}", f"answer {i}")
    assert len(history.turns) == 3
    # only the most recent 3 should remain
    assert history.turns[0].question == "question 2"
    assert history.turns[-1].question == "question 4"