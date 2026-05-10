from __future__ import annotations

import json
from pathlib import Path

from models.message import Message
from services.chat_service import ChatService
from services.content_service import ContentService
from services.safety_service import SafetyService


class _FakeFunction:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, call_id: str, name: str, arguments: str) -> None:
        self.id = call_id
        self.function = _FakeFunction(name=name, arguments=arguments)


class _FakeAssistantMessage:
    def __init__(self, content: str = "", tool_calls=None) -> None:
        self.content = content
        self.tool_calls = tool_calls


class _FakeClient:
    def __init__(self, responses) -> None:
        self._responses = list(responses)
        self.calls = []

    def chat_completion_message(self, messages, tools=None, tool_choice=None):
        self.calls.append({"messages": messages, "tools": tools, "tool_choice": tool_choice})
        return self._responses.pop(0)


def _setup_content(tmp_path: Path) -> ContentService:
    content_root = tmp_path / "content"
    content_root.mkdir(parents=True, exist_ok=True)
    (content_root / "about.md").write_text(
        "# About\n\nThis site covers AI tooling and Streamlit projects.\n",
        encoding="utf-8",
    )
    (content_root / "posts").mkdir(exist_ok=True)
    (content_root / "posts" / "intro.md").write_text(
        "# Intro Post\n\nThe assistant uses OpenRouter and tool calls.\n",
        encoding="utf-8",
    )
    return ContentService(content_dir="content", repo_root=tmp_path)


def test_chat_service_executes_tool_calls(tmp_path: Path):
    content_service = _setup_content(tmp_path)
    fake_client = _FakeClient(
        responses=[
            _FakeAssistantMessage(
                tool_calls=[
                    _FakeToolCall(
                        call_id="call_1",
                        name="lookup_articles",
                        arguments=json.dumps({"query": "streamlit", "limit": 2}),
                    ),
                    _FakeToolCall(
                        call_id="call_2",
                        name="get_article",
                        arguments=json.dumps({"slug": "about"}),
                    ),
                ]
            ),
            _FakeAssistantMessage(content="The About page explains this site focuses on AI tooling and Streamlit."),
        ]
    )

    service = ChatService(client=fake_client, content_service=content_service)
    reply = service.process_message(Message(content="What is this website about?", sender="User"))

    assert "streamlit" in reply.content.lower()
    assert len(fake_client.calls) == 2
    first_call = fake_client.calls[0]
    assert first_call["tools"] is not None
    second_call_messages = fake_client.calls[1]["messages"]
    tool_messages = [m for m in second_call_messages if m.get("role") == "tool"]
    assert len(tool_messages) == 2


def test_chat_service_applies_safety_filters(tmp_path: Path):
    content_service = _setup_content(tmp_path)
    fake_client = _FakeClient(responses=[_FakeAssistantMessage(content="unused")])
    safety = SafetyService(mode="strict", blocked_terms=["exploit"], max_user_chars=300)
    service = ChatService(client=fake_client, content_service=content_service, safety_service=safety)

    reply = service.process_message(Message(content="Please provide an exploit for this app.", sender="User"))
    assert "can't help" in reply.content.lower()
    assert fake_client.calls == []
