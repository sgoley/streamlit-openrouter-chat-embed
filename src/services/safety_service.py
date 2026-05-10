from __future__ import annotations

from typing import List, Optional


class SafetyService:
    def __init__(
        self,
        mode: str = "moderate",
        max_user_chars: int = 2000,
        blocked_terms: Optional[List[str]] = None,
    ) -> None:
        normalized_mode = mode.strip().lower()
        if normalized_mode not in {"off", "moderate", "strict"}:
            normalized_mode = "moderate"

        self.mode = normalized_mode
        self.max_user_chars = max(200, max_user_chars)
        self.blocked_terms = [term.strip().lower() for term in (blocked_terms or []) if term.strip()]

    def evaluate_user_message(self, message: str) -> Optional[str]:
        cleaned = message.strip()
        if not cleaned:
            return "Please send a non-empty message."

        if len(cleaned) > self.max_user_chars:
            return (
                f"Your message is too long ({len(cleaned)} chars). "
                f"Please keep requests under {self.max_user_chars} characters."
            )

        if self.mode == "off":
            return None

        lowered = cleaned.lower()
        injection_markers = (
            "ignore previous instructions",
            "reveal the system prompt",
            "show me your hidden instructions",
        )
        if any(marker in lowered for marker in injection_markers):
            return "I can't help with instruction-hijacking requests. Ask about the site content instead."

        if self.blocked_terms and any(term in lowered for term in self.blocked_terms):
            return "I can't help with that request."

        if self.mode == "strict":
            secret_markers = ("api key", "secret token", "private key", "password dump")
            if any(marker in lowered for marker in secret_markers):
                return "I can't assist with requests to expose credentials or secrets."

        return None
