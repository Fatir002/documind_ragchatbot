"""Try multi-turn Q&A: python -m scripts.try_qa"""

from app.exceptions import DocuMindError
from app.qa.chain import answer_question
from app.qa.history import ConversationHistory


def main() -> None:
    history = ConversationHistory()
    print("Ask a question (or 'quit'):")
    while True:
        question = input("> ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        try:
            answer = answer_question(question, history)
        except DocuMindError as exc:
            print(f"❌ {exc.user_message}")
            continue

        print("\nANSWER:", answer.text)
        for number, chunk in enumerate(answer.sources, start=1):
            page = chunk.metadata.get("page", "?")
            print(f"  [{number}] {chunk.metadata.get('source')}, page {page}")
        print()
        history.add(question, answer.text)


if __name__ == "__main__":
    main()
