"""Unit tests for Qdrant Hybrid Retrieval and Embeddings."""

import pytest
import numpy as np
from src.vectorstore.qdrant_store import FastSemanticEmbedder, expand_query_text
from src.graph.nodes import qdrant_store

def test_fast_semantic_embedder():
    embedder = FastSemanticEmbedder(dim=384)
    q1 = expand_query_text("daily meal allowance policy")
    q2 = expand_query_text("employee dinner expense limits")
    q3 = expand_query_text("cryptographic asymmetric key rotation")

    vec1 = embedder.embed_text(q1)
    vec2 = embedder.embed_text(q2)
    vec3 = embedder.embed_text(q3)

    assert len(vec1) == 384
    assert len(vec2) == 384
    assert len(vec3) == 384

    # Cosine similarity between semantically related expanded queries should exceed unrelated queries
    sim_related = np.dot(vec1, vec2)
    sim_unrelated = np.dot(vec1, vec3)
    assert sim_related > sim_unrelated

def test_qdrant_hybrid_search():
    # Use existing singleton store to avoid lock collision
    results = qdrant_store.hybrid_search("hotel lodging ceiling per night", limit=5)
    assert len(results) > 0
    assert "rrf_score" in results[0]
    assert "payload" in results[0]
    assert "document_id" in results[0]["payload"]
