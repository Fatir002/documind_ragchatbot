"""Try the Q&A chain: python -m scripts.try_qa "your question" """

import sys

from app.exceptions import DocuMindError
from app.qa.chain import answer_question


def main() -> None:
    question = sys.argv[1]
    try:
        answer = answer_question(question)
    except DocuMindError as exc:
        print(f"❌ The user would see: {exc.user_message}")
        return

    print("ANSWER:")
    print(answer.text)
    print("\nSOURCES:")
    for number, chunk in enumerate(answer.sources, start=1):
        page = chunk.metadata.get("page", "?")
        print(f"  [{number}] {chunk.metadata.get('source')}, page {page}")


if __name__ == "__main__":
    main()
