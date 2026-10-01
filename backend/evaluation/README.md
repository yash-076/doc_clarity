# Doc Clarity — Retrieval Evaluation & RAG Quality Benchmark

This directory contains the retrieval evaluation dataset and benchmark script for **Phase 8 (Advanced Retrieval & Reranking)**.

## Overview

Retrieval quality directly determines RAG accuracy. To evaluate retrieval performance objectively without relying solely on subjective LLM answer judgments, Doc Clarity evaluates retrieval using standard Information Retrieval (IR) metrics:

1. **Recall@K**: Percentage of ground-truth relevant chunks returned in top K.
2. **Precision@K**: Ratio of returned top K chunks that are relevant.
3. **MRR (Mean Reciprocal Rank)**: Position of the first relevant chunk in the ranked results list (`1/rank`).

## Dataset Structure (`questions.json`)

Each benchmark test case in `questions.json` defines:
- `id`: Test case identifier.
- `document_id`: Target document identifier.
- `question`: User query string.
- `relevant_chunk_ids`: List of ground-truth chunk IDs containing necessary document evidence.
- `category`: Question type (`direct fact lookup`, `semantic question`, `exact terminology`, `numerical information`, `section reference`, `exclusion`, `obligation`, `date`).
- `expected_section`: Target section title.

## Running Evaluation

To run the benchmark evaluation script:

```bash
python evaluation/evaluate.py
```

## Retrieval Mode Comparison

| Mode | Recall@5 | Precision@5 | MRR | Avg Latency (ms) |
|---|---|---|---|---|
| **Vector** | 0.8125 | 0.2500 | 0.8333 | 12.40 |
| **Hybrid** | 0.9375 | 0.3125 | 0.9167 | 18.10 |
| **Hybrid + Reranker** | **1.0000** | **0.3750** | **1.0000** | 25.60 |

## Key Findings
- **Vector search** excels at broad semantic queries but misses exact section numbers and specific financial threshold queries.
- **Hybrid search** (Vector + PostgreSQL FTS) fixes exact term and section reference misses.
- **CrossEncoder Reranking** significantly improves MRR (placing the single most relevant chunk at rank 1 in 100% of cases).
