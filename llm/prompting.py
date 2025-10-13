"""
Utilities for prompt rendering and answering queries from chunks.

This module provides helper functions to:
- Validate and render prompt templates that contain the required
  placeholders: "{{chunks}}" and "{{query}}".
- Build chat messages for LLMs from a rendered prompt.
- Generate an answer using the configured LLM from provided chunks and query.

Notes:
- Prompts MUST include both "{{chunks}}" and "{{query}}". A ValueError is raised otherwise.
- Chunks are formatted with simple numbering by default. You can pre-format
  them yourself and pass as a single string if you need custom layout.
"""
from __future__ import annotations

from typing import List, Dict, Optional, Union

from .interfaces import LLMInterface
from .model_factory import get_llm


def _ensure_placeholders(prompt_template: str) -> None:
    """Ensure prompt contains required placeholders.

    Raises:
        ValueError: If either placeholder is missing.
    """
    missing: List[str] = []
    if "{{query}}" not in prompt_template:
        missing.append("{{query}}")
    if "{{chunks}}" not in prompt_template:
        missing.append("{{chunks}}")
    if missing:
        raise ValueError(f"Prompt template missing required placeholders: {', '.join(missing)}")


def format_chunks(chunks: List[str]) -> str:
    """Format a list of chunk strings for insertion into a prompt.

    The default formatting enumerates chunks for easier reference.
    """
    if not chunks:
        return "(no chunks available)"
    lines: List[str] = []
    for idx, ch in enumerate(chunks, start=1):
        # Keep it plain-text and deterministic
        lines.append(f"[Chunk {idx}]\n{ch}")
    return "\n\n".join(lines)


def render_prompt_text(prompt_template: str, chunks: List[str], query: str) -> str:
    """Render a prompt by replacing required placeholders with values.

    Args:
        prompt_template: Template that must contain "{{chunks}}" and "{{query}}".
        chunks: Context chunks to insert.
        query: The user query/question.

    Returns:
        The final prompt string with placeholders replaced.
    """
    _ensure_placeholders(prompt_template)
    formatted_chunks = format_chunks(chunks)
    # Simple, literal replacement (do not use .format to avoid brace semantics)
    prompt = prompt_template.replace("{{chunks}}", formatted_chunks).replace("{{query}}", query)
    return prompt


def build_messages_for_prompt(
    prompt_template: str,
    chunks: List[str],
    query: str,
    system_prompt: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Build OpenAI-style chat messages from a prompt template and inputs.

    By default, the rendered prompt is sent as a single user message. You may
    pass an optional system prompt to bias behavior without altering the saved
    template for the test.
    """
    user_content = render_prompt_text(prompt_template, chunks, query)
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_content})
    return messages


async def answer_query_from_chunks(
    llm: Union[LLMInterface, str],
    prompt_template: str,
    chunks: List[str],
    query: str,
    *,
    system_prompt: Optional[str] = None,
    **generate_kwargs,
) -> str:
    """Answer a query using an LLM, a prompt template, and retrieved chunks.

    Args:
        llm: Either an LLMInterface instance or a model name (e.g., 'openai_4o').
        prompt_template: Template that includes "{{chunks}}" and "{{query}}".
        chunks: List of chunk strings to insert into the prompt.
        query: The user query/question.
        system_prompt: Optional system message to prepend.
        **generate_kwargs: Additional kwargs forwarded to LLM.generate (e.g., temperature, max_tokens).

    Returns:
        The model's answer text.
    """
    model: LLMInterface
    if isinstance(llm, str):
        model = get_llm(llm)
    else:
        model = llm

    messages = build_messages_for_prompt(prompt_template, chunks, query, system_prompt=system_prompt)
    return await model.generate(messages, **generate_kwargs)

