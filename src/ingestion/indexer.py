"""Enterprise Ingestion and Indexing Pipeline.
Processes 200+ enterprise documents, chunks them by section, indexes vectors into Qdrant,
and compiles structured policy constraints into SQLite.
"""

import time
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table

from src.config import settings
from src.corpus.loader import load_all_policies
from src.ingestion.chunker import EnterprisePolicyChunker
from src.vectorstore.qdrant_store import QdrantHybridStore
from src.sql_engine.database import get_connection, init_db

console = Console()

def run_indexing_pipeline() -> Dict[str, Any]:
    """Runs the full indexing pipeline: chunking -> Qdrant vectorstore -> SQLite rules."""
    start_time = time.perf_counter()
    console.print("[bold green]Starting PolicyGuard Enterprise Ingestion Pipeline...[/bold green]")

    # 1. Initialize DB
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # 2. Load policies
    docs = load_all_policies()
    if not docs:
        console.print("[yellow]No policies found! Generating corpus first...[/yellow]")
        from src.corpus.generator import build_corpus
        build_corpus()
        docs = load_all_policies()

    console.print(f"[cyan]Loaded {len(docs)} multi-page enterprise policy documents.[/cyan]")

    # 3. Chunk documents
    chunker = EnterprisePolicyChunker(target_chunk_size=500, chunk_overlap=80)
    all_chunks = []
    rule_records = []

    for doc in docs:
        doc_meta = {
            "document_id": doc.get("document_id"),
            "title": doc.get("title"),
            "category": doc.get("category"),
            "jurisdiction": doc.get("jurisdiction"),
            "version": doc.get("version"),
            "authorizer": doc.get("authorizer")
        }
        body = doc.get("body", "")
        chunks = chunker.chunk_document(doc_meta, body)
        all_chunks.extend(chunks)

        # Extract structured rule for SQLite policy_rules table
        doc_id = doc.get("document_id")
        category = doc.get("category", "")
        jurisdiction = doc.get("jurisdiction", "Global")
        version = doc.get("version", "v1.0")

        # Parse key quantifiable metric from body if present
        import re
        param_match = re.search(r"Parameter:\s*`([^`]+)`", body)
        thresh_match = re.search(r"Formal Threshold / Value:\s*\*\*([^\*]+)\*\*", body)
        rule_key = param_match.group(1) if param_match else f"{category}_rule"
        thresh_str = thresh_match.group(1) if thresh_match else "standard"

        try:
            val_num = float(thresh_str.replace("$", "").replace(",", ""))
        except ValueError:
            val_num = None

        rule_records.append((
            doc_id,
            category,
            rule_key,
            val_num,
            thresh_str,
            f"{doc.get('title')} ({category})",
            jurisdiction,
            version
        ))

    # Insert into SQLite policy_rules
    cursor.executemany("""
        INSERT OR REPLACE INTO policy_rules
        (policy_id, category, rule_key, rule_value, rule_value_str, description, jurisdiction, version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rule_records)
    conn.commit()
    conn.close()

    console.print(f"[cyan]Created {len(all_chunks)} section-aware chunks across 200+ policies.[/cyan]")
    console.print(f"[cyan]Compiled {len(rule_records)} structured rules into SQLite engine.[/cyan]")

    # 4. Index into Qdrant
    qdrant_store = QdrantHybridStore()
    indexed_points = qdrant_store.upsert_chunks(all_chunks)

    elapsed_s = time.perf_counter() - start_time
    console.print(f"[bold green]Successfully indexed {indexed_points} chunks into Qdrant in {elapsed_s:.2f}s![/bold green]")

    # Display summary table
    table = Table(title="PolicyGuard Ingestion Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Enterprise Documents", str(len(docs)))
    table.add_row("Total Section Chunks", str(len(all_chunks)))
    table.add_row("Deterministic SQL Rules", str(len(rule_records)))
    table.add_row("Qdrant Collection", settings.qdrant_collection)
    table.add_row("Indexing Duration", f"{elapsed_s:.2f} seconds")

    console.print(table)

    return {
        "documents_count": len(docs),
        "chunks_count": len(all_chunks),
        "rules_count": len(rule_records),
        "duration_seconds": round(elapsed_s, 2)
    }

if __name__ == "__main__":
    run_indexing_pipeline()

