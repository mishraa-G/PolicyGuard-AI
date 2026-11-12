"""Hierarchical Section-Aware Chunker for Enterprise Policies.
Preserves header hierarchies, structured frontmatter, and quantifiable bounds in chunk metadata.
"""

import re
from typing import List, Dict, Any

class EnterprisePolicyChunker:
    def __init__(self, target_chunk_size: int = 500, chunk_overlap: int = 100):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc_metadata: Dict[str, Any], body_text: str) -> List[Dict[str, Any]]:
        """Splits markdown policy documents by section while preserving contextual metadata."""
        chunks = []
        doc_id = doc_metadata.get("document_id", "DOC-UNKNOWN")
        category = doc_metadata.get("category", "general")
        jurisdiction = doc_metadata.get("jurisdiction", "Global")
        version = doc_metadata.get("version", "v1.0")
        title = doc_metadata.get("title", "")

        # Split by markdown headers ##
        sections = re.split(r"\n(?=##\s+)", body_text)

        chunk_seq = 0
        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Skip standalone title header without substantive body
            if section.startswith("# ") and "##" not in section and len(section.splitlines()) <= 2:
                continue

            # Extract section heading
            header_match = re.match(r"^##\s+(.*?)\n", section)
            section_name = header_match.group(1).strip() if header_match else "General Provisions"

            # Always embed document title and section context into chunk text
            prefix = f"Policy {doc_id}: {title} | {section_name}\n"
            content_body = section

            chunk_id = f"{doc_id}-chunk-{chunk_seq:02d}"
            chunks.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "title": title,
                "category": category,
                "jurisdiction": jurisdiction,
                "version": version,
                "section": section_name,
                "text": f"{prefix}{content_body}".strip(),
                "word_count": len(content_body.split())
            })
            chunk_seq += 1

        return chunks
