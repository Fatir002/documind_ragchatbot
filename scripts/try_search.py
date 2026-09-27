"""Try search: python -m scripts.try_search "query" [vector|keyword|hybrid]"""

import sys

from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.keyword_search import keyword_search
from app.retrieval.vector_search import vector_search

MODES = {"vector": vector_search, "keyword": keyword_search, "hybrid": hybrid_search}


def main() -> None:
    query = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "hybrid"
    results = MODES[mode](query, limit=5)

    if not results:
        print("No chunks found.")
        return
    for rank, chunk in enumerate(results, start=1):
        print(f"{rank}. score={chunk.score:.4f}  {chunk.metadata}")
        print("   ", chunk.content[:120].replace("\n", " "))


if __name__ == "__main__":
    main()
