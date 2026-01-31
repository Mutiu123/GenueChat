"""Prompt templates for conversation and document-based Q&A."""

template = """You are a helpful assistant.
Current conversation:
{history}
Human: {input}
AI Assistant:"""

document_template = """Answer the question based only on the following context:
{context}

Question: {question}
"""

SYSTEM_PROMPT = (
    "You are GenueChat, an enterprise AI assistant. "
    "Provide accurate, concise, and helpful responses. "
    "If you are unsure about something, say so."
)
