"""Small retrieval/generation smoke evaluation over the sample corpus.

Usage:
    python scripts/evaluate.py
    python scripts/evaluate.py --json

This is intentionally a tiny, deterministic evaluation, not a benchmark. It checks
that the expected document is retrieved, that the answer contains the key fact,
and that at least one citation is returned.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Settings
from src.embeddings import create_embedder
from src.generate import GroundedGenerator
from src.retrieve import Retriever
from src.vector_store import create_vector_store

QUESTIONS: list[dict[str, Any]] = [
    {
        "question": "How many PTO days do employees get?",
        "source": "company-handbook.md",
        "fact": "20 days",
    },
    {
        "question": "How many weeks of parental leave do primary caregivers get?",
        "source": "company-handbook.md",
        "fact": "16 weeks",
    },
    {
        "question": "What is the first response time for a P1 ticket?",
        "source": "customer-support-playbook.md",
        "fact": "15 minutes",
    },
    {
        "question": "What is the refund window?",
        "source": "customer-support-playbook.md",
        "fact": "30 days",
    },
    {
        "question": "How much can I spend on a hotel in India?",
        "source": "expense-and-travel-policy.md",
        "fact": "8,000",
    },
    {
        "question": "What should I do if my laptop is stolen?",
        "source": "information-security-policy.md",
        "fact": "one hour",
    },
    {
        "question": "Can I use customer data in a public AI tool?",
        "source": "information-security-policy.md",
        "fact": "public",
    },
    {
        "question": "Does Orbit support SAML SSO?",
        "source": "orbit-product-faq.md",
        "fact": "SAML",
    },
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    embedder = create_embedder(settings)
    store = create_vector_store(settings, embedder)
    if store.count() == 0:
        print("Vector store is empty. Run `python -m src.ingest` first.", file=sys.stderr)
        return 1

    retriever = Retriever(settings, store, embedder)
    generator = GroundedGenerator(settings)

    results: list[dict[str, Any]] = []
    for item in QUESTIONS:
        chunks = retriever.retrieve(item["question"])
        answer = generator.generate(item["question"], chunks)
        retrieval_hit = any(chunk.source == item["source"] for chunk in chunks)
        answer_has_fact = item["fact"].lower() in answer.text.lower()
        has_citation = bool(answer.citations)
        results.append(
            {
                **item,
                "retrieval_hit": retrieval_hit,
                "answer_has_fact": answer_has_fact,
                "has_citation": has_citation,
                "top_source": chunks[0].source if chunks else None,
                "answer": answer.text,
                "mode": answer.mode,
                "passed": retrieval_hit and answer_has_fact and has_citation,
            }
        )

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        print(f"{'PASS':<5} {'RETRIEVAL':<10} {'FACT':<5} {'CITE':<5} QUESTION")
        print("-" * 100)
        for result in results:
            print(
                f"{'yes' if result['passed'] else 'NO':<5} "
                f"{'yes' if result['retrieval_hit'] else 'NO':<10} "
                f"{'yes' if result['answer_has_fact'] else 'NO':<5} "
                f"{'yes' if result['has_citation'] else 'NO':<5} "
                f"{result['question']}"
            )
        passed = sum(1 for result in results if result["passed"])
        print("-" * 100)
        print(f"{passed}/{len(results)} checks passed | mode={results[0]['mode']}")
        print("Tip: install requirements.txt and configure an LLM key for natural-language answers.")

    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
