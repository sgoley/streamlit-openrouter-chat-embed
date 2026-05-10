from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContentService:
    def __init__(self, content_dir: str = "content", repo_root: Optional[Path] = None) -> None:
        base_root = (repo_root or Path.cwd()).resolve()
        allowed_root = (base_root / "content").resolve()
        configured_path = Path(content_dir).expanduser()
        resolved_path = (
            configured_path if configured_path.is_absolute() else base_root / configured_path
        ).resolve()
        try:
            resolved_path.relative_to(allowed_root)
        except ValueError as exc:
            raise ValueError(
                "CONTENT_DIR must stay within the repository content/ directory."
            ) from exc

        self.content_root = resolved_path
        self.repo_root = base_root

    @property
    def display_path(self) -> str:
        try:
            return str(self.content_root.relative_to(self.repo_root))
        except ValueError:
            return str(self.content_root)

    def list_articles(self) -> List[Dict[str, str]]:
        return [
            {
                "slug": item["slug"],
                "title": item["title"],
                "relative_path": item["relative_path"],
            }
            for item in self._load_articles()
        ]

    def get_article(self, slug: str) -> Optional[Dict[str, str]]:
        normalized_slug = slug.strip().strip("/")
        for item in self._load_articles():
            if item["slug"] == normalized_slug:
                return item
        return None

    def search_articles(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        cleaned_query = query.strip().lower()
        if not cleaned_query:
            return []

        terms = [term for term in re.split(r"\s+", cleaned_query) if term]
        scored: List[tuple[int, Dict[str, str]]] = []

        for item in self._load_articles():
            title_text = item["title"].lower()
            body_text = item["content"].lower()
            score = 0
            for term in terms:
                score += title_text.count(term) * 4
                score += body_text.count(term)
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: (-pair[0], pair[1]["title"]))
        results: List[Dict[str, str]] = []
        for _, article in scored[: max(1, min(limit, 10))]:
            results.append(
                {
                    "slug": article["slug"],
                    "title": article["title"],
                    "relative_path": article["relative_path"],
                    "excerpt": article["excerpt"],
                }
            )
        return results

    def _load_articles(self) -> List[Dict[str, str]]:
        if not self.content_root.exists() or not self.content_root.is_dir():
            return []

        articles: List[Dict[str, str]] = []
        for file_path in sorted(self.content_root.rglob("*.md")):
            if not file_path.is_file():
                continue
            content = file_path.read_text(encoding="utf-8")
            relative_path = str(file_path.relative_to(self.content_root)).replace("\\", "/")
            slug = relative_path.rsplit(".", 1)[0]
            title = self._extract_title(content, fallback=file_path.stem)
            articles.append(
                {
                    "slug": slug,
                    "title": title,
                    "relative_path": relative_path,
                    "content": content,
                    "excerpt": self._excerpt(content),
                }
            )
        return articles

    def _extract_title(self, content: str, fallback: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return fallback.replace("-", " ").replace("_", " ").title()

    def _excerpt(self, content: str, max_chars: int = 240) -> str:
        compact = " ".join(line.strip() for line in content.splitlines() if line.strip())
        return compact[:max_chars] + ("..." if len(compact) > max_chars else "")
