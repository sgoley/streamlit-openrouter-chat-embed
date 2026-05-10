from __future__ import annotations

from pathlib import Path

import pytest
from services.content_service import ContentService


def _create_content_tree(tmp_path: Path) -> ContentService:
    content_dir = tmp_path / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    (content_dir / "welcome.md").write_text(
        "# Welcome Post\n\nThis site is built with Streamlit and OpenRouter.\n",
        encoding="utf-8",
    )
    (content_dir / "deep-dive.md").write_text(
        "# Deep Dive\n\nThis article discusses tool calls and markdown retrieval.\n",
        encoding="utf-8",
    )
    return ContentService(content_dir="content", repo_root=tmp_path)


def test_list_and_get_articles(tmp_path: Path):
    service = _create_content_tree(tmp_path)

    listing = service.list_articles()
    assert len(listing) == 2
    assert any(item["slug"] == "welcome" for item in listing)

    welcome = service.get_article("welcome")
    assert welcome is not None
    assert "Streamlit" in welcome["content"]


def test_search_articles_returns_ranked_matches(tmp_path: Path):
    service = _create_content_tree(tmp_path)
    results = service.search_articles("markdown retrieval", limit=2)

    assert len(results) >= 1
    assert results[0]["slug"] == "deep-dive"


def test_content_service_rejects_paths_outside_content_directory(tmp_path: Path):
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)
    with pytest.raises(ValueError, match="CONTENT_DIR"):
        ContentService(content_dir=str(outside_dir), repo_root=tmp_path)
