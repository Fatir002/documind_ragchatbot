"""In-memory conversation history for a single chat session."""

from dataclasses import dataclass, field


@dataclass
class Turn:
    """One question-answer exchange."""

    question: str
    answer: str


@dataclass
class ConversationHistory:
    """Holds recent turns for one session. Not persisted across app restarts."""

    turns: list[Turn] = field(default_factory=list)
    max_turns: int = 6  # keep the prompt small; older turns are dropped

    def add(self, question: str, answer: str) -> None:
        self.turns.append(Turn(question=question, answer=answer))
        self.turns = self.turns[-self.max_turns :]

    def as_text(self) -> str:
        """Render history as plain text for the query-rewriting prompt."""
        if not self.turns:
            return ""
        lines = [f"User: {t.question}\nAssistant: {t.answer}" for t in self.turns]
        return "\n\n".join(lines)
