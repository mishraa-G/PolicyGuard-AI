"""Corpus loader module for reading and parsing enterprise policy documents."""

import re
from pathlib import Path
from typing import List, Dict, Any
from src.config import settings

def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Extracts YAML-style frontmatter and body markdown."""
    frontmatter = {}
    body = content

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if fm_match:
        fm_block, body = fm_match.groups()
        for line in fm_block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                frontmatter[key] = val

    return frontmatter, body.strip()

def load_all_policies(corpus_dir: Path = None) -> List[Dict[str, Any]]:
    """Loads all policy markdown files from the corpus directory."""
    if corpus_dir is None:
        corpus_dir = settings.raw_policies_dir

    policies = []
    if not corpus_dir.exists():
        return policies

    for file_path in corpus_dir.rglob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            metadata, body = parse_frontmatter(content)
            metadata["file_path"] = str(file_path)
            metadata["full_text"] = content
            metadata["body"] = body
            policies.append(metadata)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    policies.sort(key=lambda x: x.get("document_id", ""))
    return policies

if __name__ == "__main__":
    docs = load_all_policies()
    print(f"Loaded {len(docs)} policy documents.")

