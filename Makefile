.PHONY: help install generate-corpus index eval benchmark test api clean

help:
	@echo "PolicyGuard Enterprise Compliance RAG CLI"
	@echo "----------------------------------------"
	@echo "make generate-corpus : Generate 200+ multi-page enterprise policy documents & SQL rules"
	@echo "make index           : Build Qdrant hybrid vector store & SQL database"
	@echo "make eval            : Run Ragas-style automated evaluation benchmark (Recall & Hallucination rate)"
	@echo "make benchmark       : Run sub-800ms latency profiler and distribution analysis"
	@echo "make test            : Run test suite via pytest"
	@echo "make api             : Start FastAPI server on port 8000"
	@echo "make demo            : Run interactive CLI demo"

generate-corpus:
	.venv/bin/python -m src.corpus.generator

index:
	.venv/bin/python -m src.ingestion.indexer

eval:
	.venv/bin/python -m evaluation.run_eval

benchmark:
	.venv/bin/python -m benchmarks.latency_profiler

test:
	.venv/bin/pytest tests/ -v

api:
	.venv/bin/uvicorn src.api.app:app --host 0.0.0.0 --port 8001 --reload

demo:
	.venv/bin/python main.py

clean:
	rm -rf qdrant_storage data/policy_database.sqlite .pytest_cache __pycache__

