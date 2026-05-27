#!/usr/bin/env python3
"""CLI evaluation runner for Recall@k assessment.

Usage:
    python scripts/evaluate.py --test-file tests/fixtures/test_queries.json --k 1,3,5,10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.config import load_settings
from app.core.logging import setup_logging
from app.models import create_engine_and_session
from app.services.dedup_service import DedupService
from app.services.embedding_service import EmbeddingService
from app.services.evaluator import EvalQuery, Evaluator
from app.services.search_service import SearchService
from app.vectorstore import get_vector_store


def load_test_queries(file_path: str) -> list[EvalQuery]:
    """Load test queries from a JSON file.

    Expected format:
    [
        {
            "query": "How to reset password?",
            "relevant_doc_ids": ["uuid1", "uuid2"],
            "language": "en"
        },
        ...
    ]
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    return [
        EvalQuery(
            query=item["query"],
            relevant_doc_ids=item["relevant_doc_ids"],
            language=item.get("language", "unknown"),
        )
        for item in data
    ]


async def run_evaluation(test_file: str, k_values: list[int]) -> None:
    """Run the evaluation and print results."""
    settings = load_settings()
    setup_logging(settings)

    _, session_factory = create_engine_and_session(settings)
    vector_store = get_vector_store(settings)
    embedding_service = EmbeddingService(settings)
    await embedding_service.startup()

    search_service = SearchService(settings, embedding_service, vector_store)
    evaluator = Evaluator(search_service)

    queries = load_test_queries(test_file)
    print(f"Loaded {len(queries)} test queries from {test_file}")

    result = await evaluator.evaluate(queries, k_values=k_values)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total queries: {result['total_queries']}")
    print(f"\nOverall Recall:")
    for k, v in result["overall_recall"].items():
        print(f"  {k}: {v:.4f}")

    if result["per_language"]:
        print("\nPer-Language Recall:")
        for lang, stats in result["per_language"].items():
            print(f"  [{lang}] ({stats['query_count']} queries):")
            for k, v in stats["recall"].items():
                print(f"    {k}: {v:.4f}")

    badcases = result["badcases"]
    if badcases:
        print(f"\nBadcases (Recall@5 < 0.5): {len(badcases)}")
        for bc in badcases[:10]:
            print(f"  - '{bc['query']}' [{bc['language']}] Recall@5={bc['recall_at_5']:.4f}")
        if len(badcases) > 10:
            print(f"  ... and {len(badcases) - 10} more")

    print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(description="CaraBot Evaluation Runner")
    parser.add_argument(
        "--test-file",
        required=True,
        help="Path to JSON file with test queries",
    )
    parser.add_argument(
        "--k",
        default="1,3,5,10",
        help="Comma-separated K values for Recall@k (default: 1,3,5,10)",
    )
    args = parser.parse_args()

    k_values = [int(k.strip()) for k in args.k.split(",")]
    asyncio.run(run_evaluation(args.test_file, k_values))


if __name__ == "__main__":
    main()
