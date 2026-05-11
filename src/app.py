import html
import os
from pathlib import Path

import markdown as md
import streamlit as st
from api.openrouter_client import OpenRouterClient
from dotenv import load_dotenv
from models.message import Message
from services.chat_service import ChatService
from services.content_service import ContentService
from services.safety_service import SafetyService

# Load .env file if present
load_dotenv()

st.set_page_config(
    page_title="Website Chat",
    page_icon=":speech_balloon:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root {
    --bg: #000000;
    --panel: #111214;
    --ink: #f5f5f7;
    --muted: #a6a6ad;
    --assistant: #2c2c2e;
    --user: #0a84ff;
    --line: rgba(255, 255, 255, 0.08);
}

.stApp {
    background: linear-gradient(180deg, #000000 0%, #090909 100%);
    color: var(--ink);
}

[data-testid="stSidebar"],
[data-testid="stSidebarNav"] {
    display: none;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 860px;
    padding-top: 1.1rem;
    padding-bottom: 1.4rem;
}

.chat-title {
    margin: 0;
    color: var(--ink);
    font-size: 1.35rem;
    font-weight: 700;
}

.chat-subtitle {
    margin-top: 0.25rem;
    margin-bottom: 0.6rem;
    color: var(--muted);
    font-size: 0.9rem;
}

.chat-thread {
    border: 1px solid var(--line);
    background: var(--panel);
    border-radius: 18px;
    padding: 0.9rem;
    min-height: 420px;
    max-height: 62vh;
    overflow-y: auto;
}

.message-row {
    display: flex;
    width: 100%;
    margin: 0.45rem 0;
}

.message-row.user {
    justify-content: flex-end;
}

.message-row.assistant {
    justify-content: flex-start;
}

.bubble {
    max-width: 78%;
    padding: 0.62rem 0.8rem;
    line-height: 1.42;
    font-size: 0.96rem;
    word-wrap: break-word;
    overflow-wrap: anywhere;
}

.bubble.user {
    background: var(--user);
    color: #ffffff;
    border-radius: 18px 18px 6px 18px;
}

.bubble.assistant {
    background: var(--assistant);
    color: #ffffff;
    border-radius: 18px 18px 18px 6px;
}

.bubble.assistant > :first-child {
    margin-top: 0;
}

.bubble.assistant > :last-child {
    margin-bottom: 0;
}

.bubble.assistant p,
.bubble.assistant ul,
.bubble.assistant ol,
.bubble.assistant pre,
.bubble.assistant table,
.bubble.assistant blockquote {
    margin: 0.35rem 0 0.55rem;
}

.bubble.assistant ul,
.bubble.assistant ol {
    padding-left: 1.1rem;
}

.bubble.assistant li + li {
    margin-top: 0.22rem;
}

.bubble.assistant code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    background: rgba(255, 255, 255, 0.09);
    border-radius: 6px;
    padding: 0.08rem 0.32rem;
    font-size: 0.88em;
}

.bubble.assistant pre {
    background: #18191c;
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 0.58rem 0.72rem;
    overflow-x: auto;
}

.bubble.assistant pre code {
    background: transparent;
    padding: 0;
    border-radius: 0;
}

.bubble.assistant blockquote {
    border-left: 3px solid rgba(255, 255, 255, 0.25);
    margin-left: 0;
    padding-left: 0.65rem;
    color: #d4d4d8;
}

.bubble.assistant table {
    width: 100%;
    border-collapse: collapse;
}

.bubble.assistant th,
.bubble.assistant td {
    border: 1px solid var(--line);
    padding: 0.32rem 0.45rem;
    text-align: left;
}

.bubble.assistant th {
    background: rgba(255, 255, 255, 0.06);
}

.empty-state {
    color: var(--muted);
    text-align: center;
    margin-top: 7.5rem;
    font-size: 0.94rem;
}

.stButton > button {
    border-radius: 999px;
    border: 1px solid var(--line);
    background: #1d1d20;
    color: var(--ink);
}

[data-testid="stChatInput"] {
    margin-top: 0.65rem;
}

[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div:focus-within {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

[data-testid="stChatInput"] [data-baseweb="textarea"] {
    border: none !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] [data-baseweb="textarea"] textarea,
[data-testid="stChatInput"] textarea {
    background: #1a1a1d !important;
    color: var(--ink) !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 14px !important;
    outline: none !important;
}

[data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] textarea:focus-visible {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def _secret_get(key: str):
    # Guarded access to st.secrets (it raises if no secrets.toml exists)
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def _int_config(name: str, fallback: int) -> int:
    raw = os.getenv(name) or _secret_get(name)
    if raw is None:
        return fallback
    try:
        return int(raw)
    except (TypeError, ValueError):
        return fallback


def _render_assistant_markdown(content: str) -> str:
    # Escape raw HTML so only markdown syntax is rendered in chat bubbles.
    escaped_content = html.escape(content)
    return md.markdown(
        escaped_content,
        extensions=["fenced_code", "tables", "sane_lists", "nl2br"],
    )


def _message_html(message: Message) -> str:
    is_user = message.sender.lower() == "user"
    role = "user" if is_user else "assistant"
    if is_user:
        rendered_content = html.escape(message.content).replace("\n", "<br>")
    else:
        rendered_content = _render_assistant_markdown(message.content)
    return f"""
<div class="message-row {role}">
  <div class="bubble {role}">{rendered_content}</div>
</div>
"""


api_key = (
    os.getenv("OPENROUTER_API_KEY")
    or os.getenv("API_KEY")
    or _secret_get("OPENROUTER_API_KEY")
    or _secret_get("API_KEY")
)
model_id = (
    os.getenv("OPENROUTER_MODEL")
    or os.getenv("MODEL")
    or _secret_get("OPENROUTER_MODEL")
    or _secret_get("MODEL")
    or "openai/gpt-oss-120b"
)
referer = (
    os.getenv("OPENROUTER_HTTP_REFERER")
    or os.getenv("HTTP_REFERER")
    or _secret_get("OPENROUTER_HTTP_REFERER")
    or _secret_get("HTTP_REFERER")
)
site_title = (
    os.getenv("OPENROUTER_SITE_TITLE")
    or os.getenv("SITE_TITLE")
    or _secret_get("OPENROUTER_SITE_TITLE")
    or _secret_get("SITE_TITLE")
)
safety_mode = os.getenv("SAFETY_MODE") or _secret_get("SAFETY_MODE") or "moderate"
blocked_terms_raw = os.getenv("BLOCKED_TERMS") or _secret_get("BLOCKED_TERMS") or ""
max_user_chars = _int_config("MAX_USER_CHARS", 2000)
max_article_context_chars = _int_config("MAX_ARTICLE_CONTEXT_CHARS", 12000)

if not api_key:
    st.error(
        "API key not found. Set API_KEY (or OPENROUTER_API_KEY) in your .env or environment.\n"
        'PowerShell example:  $env:API_KEY = "sk-or-..."'
    )
    st.stop()

repo_root = Path(__file__).resolve().parent.parent

if "content_service" not in st.session_state:
    try:
        st.session_state.content_service = ContentService(
            content_dir="content",
            repo_root=repo_root,
        )
    except ValueError as err:
        st.error(str(err))
        st.stop()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_service" not in st.session_state:
    client = OpenRouterClient(
        api_key=api_key,
        model=model_id,
        referer=referer,
        site_title=site_title,
    )
    safety_service = SafetyService(
        mode=safety_mode,
        max_user_chars=max_user_chars,
        blocked_terms=[
            term.strip() for term in blocked_terms_raw.split(",") if term.strip()
        ],
    )
    st.session_state.chat_service = ChatService(
        client,
        content_service=st.session_state.content_service,
        safety_service=safety_service,
        max_article_chars=max_article_context_chars,
    )

chat_service: ChatService = st.session_state.chat_service
content_service: ContentService = st.session_state.content_service
articles = content_service.list_articles()

header_col, action_col = st.columns([5, 1], gap="small")
header_col.markdown('<h1 class="chat-title">Messages</h1>', unsafe_allow_html=True)
header_col.markdown(
    f'<p class="chat-subtitle"> ℹ️ Chat scope is locked to <code>/content</code> markdown only ({len(articles)} files indexed).</p>',
    unsafe_allow_html=True,
)
with action_col:
    if st.button("Clear", use_container_width=True):
        st.session_state.messages = []

if st.session_state.messages:
    thread_body = "".join(
        _message_html(message) for message in st.session_state.messages
    )
else:
    thread_body = '<div class="empty-state">Ask a question about your markdown content to start the conversation.</div>'
st.markdown(f'<div class="chat-thread">{thread_body}</div>', unsafe_allow_html=True)

prompt = st.chat_input("iMessage-style chat with your content...")

if prompt:
    user_msg = Message(content=prompt, sender="User")
    st.session_state.messages.append(user_msg)

    with st.spinner("Typing..."):
        try:
            reply = chat_service.process_message(
                user_msg, history=st.session_state.messages[:-1]
            )
        except Exception as err:
            st.error(f"Request failed: {err}\nTip: ensure MODEL=openai/gpt-oss-120b")
            st.stop()

    st.session_state.messages.append(reply)
    st.rerun()
