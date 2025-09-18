import streamlit as st
import anthropic
from typing import Iterable, List, Dict, Optional


DEFAULT_SYSTEM_PROMPT: str = (
    "You are a helpful data assistant for the Judge.me Marketing Dashboard. "
    "Answer concisely and clearly. When discussing metrics, prefer recent trends, "
    "note week-over-week deltas when relevant, and clarify data caveats if uncertain."
)


def _build_messages(history: Optional[List[Dict[str, str]]], prompt: str) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    if history:
        # Limit to latest 12 turns to keep within token limits
        for message in history[-12:]:
            role = message.get("role", "user")
            role = "assistant" if role == "assistant" else "user"
            content = message.get("content", "")
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    return messages


def chatbot(prompt: str, history: Optional[List[Dict[str, str]]] = None, system_context: Optional[str] = None) -> str:
    """Non-streaming chat completion.

    Returns the assistant's full response text. 
    """
    client = anthropic.Anthropic(api_key=st.secrets["claude_api_key"])
    system_text = system_context or DEFAULT_SYSTEM_PROMPT
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        system=system_text,
        messages=_build_messages(history, prompt),
        max_tokens=1000,
    )
    return response.content[0].text if response and response.content else ""


def stream_chatbot(
    prompt: str,
    history: Optional[List[Dict[str, str]]] = None,
    system_context: Optional[str] = None,
) -> Iterable[str]:
    """Streaming chat completion that yields partial text chunks."""
    client = anthropic.Anthropic(api_key=st.secrets["claude_api_key"])
    system_text = system_context or DEFAULT_SYSTEM_PROMPT

    with client.messages.stream(
        model="claude-3-5-sonnet-20240620",
        system=system_text,
        messages=_build_messages(history, prompt),
        max_tokens=1000,
    ) as stream:
        for event in stream:
            # content_block_delta events carry incremental text
            if getattr(event, "type", "") == "content_block_delta":
                delta = getattr(event, "delta", None)
                if delta and hasattr(delta, "text") and delta.text:
                    yield delta.text
