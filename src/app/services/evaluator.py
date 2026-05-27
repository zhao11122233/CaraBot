"""Recall@k evaluation and badcase analysis.

Evaluates retrieval quality by computing Recall@k against ground-truth
annotations, with support for per-language breakdown.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.app.services.search_service import SearchService

logger = logging.getLogger(__name__)


@dataclass
class EvalQuery:
    """A single test query with ground-truth document IDs."""

    query: str
    relevant_doc_ids: list[str]
    language: str = "unknown"


@dataclass
class EvalResult:
    """Result for a single query evaluation."""

    query: str
    language: str
    recall_at_k: dict[int, float] = field(default_factory=dict)
    retrieved_doc_ids: list[str] = field(default_factory=list)
    is_badcase: bool = False


class Evaluator:
    """Evaluates retrieval quality using Recall@k metric."""

    def __init__(self, search_service: SearchService) -> None:
        self._search_service = search_service

    async def evaluate(
        self,
        test_queries: list[EvalQuery],
        k_values: list[int] | None = None,
        threshold: float | None = None,
    ) -> dict:
        """Run evaluation across all test queries.

        Args:
            test_queries: List of queries with known relevant documents.
            k_values: K values for Recall@k. Default: [1, 3, 5, 10].
            threshold: Similarity threshold for search.

        Returns:
            Dict with overall_recall, per_query_results, badcases, and per_language breakdown.
        """
        if k_values is None:
            k_values = [1, 3, 5, 10]

        results: list[EvalResult] = []

        for eq in test_queries:
            result = await self._evaluate_one(eq, k_values, threshold)
            results.append(result)

        # Compute overall Recall@k
        overall_recall = {}
        for k in k_values:
            scores = [r.recall_at_k.get(k, 0.0) for r in results]
            overall_recall[f"recall@{k}"] = sum(scores) / len(scores) if scores else 0.0

        # Badcases: queries with Recall@5 below threshold
        badcase_threshold = 0.5
        badcases = [
            {
                "query": r.query,
                "language": r.language,
                "recall_at_5": r.recall_at_k.get(5, 0.0),
                "retrieved_ids": r.retrieved_doc_ids[:5],
            }
            for r in results
            if r.recall_at_k.get(5, 0.0) < badcase_threshold
        ]

        # Per-language breakdown
        per_language = self._compute_per_language(results, k_values)

        logger.info(
            "Evaluation complete: %d queries, Recall@5=%.3f, badcases=%d",
            len(results), overall_recall.get("recall@5", 0.0), len(badcases),
        )

        return {
            "total_queries": len(results),
            "overall_recall": overall_recall,
            "per_language": per_language,
            "badcases": badcases,
            "results": [
                {
                    "query": r.query,
                    "language": r.language,
                    "recall_at_k": r.recall_at_k,
                    "is_badcase": r.is_badcase,
                }
                for r in results
            ],
        }

    async def _evaluate_one(
        self, eq: EvalQuery, k_values: list[int], threshold: float | None
    ) -> EvalResult:
        """Evaluate a single query."""
        search_result = await self._search_service.search(
            query=eq.query,
            top_k=max(k_values),
            threshold=threshold,
        )

        retrieved_ids = [r["document_id"] for r in search_result["results"]]
        relevant_set = set(eq.relevant_doc_ids)

        recall_at_k = {}
        for k in k_values:
            retrieved_at_k = set(retrieved_ids[:k])
            hits = len(retrieved_at_k & relevant_set)
            recall_at_k[k] = hits / len(relevant_set) if relevant_set else 0.0

        return EvalResult(
            query=eq.query,
            language=eq.language,
            recall_at_k=recall_at_k,
            retrieved_doc_ids=retrieved_ids,
            is_badcase=recall_at_k.get(5, 0.0) < 0.5,
        )

    @staticmethod
    def _compute_per_language(
        results: list[EvalResult], k_values: list[int]
    ) -> dict:
        """Compute Recall@k broken down by language."""
        by_lang: dict[str, list[EvalResult]] = {}
        for r in results:
            by_lang.setdefault(r.language, []).append(r)

        per_language = {}
        for lang, lang_results in by_lang.items():
            lang_recall = {}
            for k in k_values:
                scores = [r.recall_at_k.get(k, 0.0) for r in lang_results]
                lang_recall[f"recall@{k}"] = sum(scores) / len(scores) if scores else 0.0
            per_language[lang] = {
                "query_count": len(lang_results),
                "recall": lang_recall,
            }

        return per_language
