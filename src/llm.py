"""Core LLM logic: conversation chain and RAG pipeline.

Provides both synchronous helpers (kept for backward compatibility)
and async wrappers used by the FastAPI routes.
"""

import asyncio
import logging
import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from src.prompts import document_template, template

logger = logging.getLogger(__name__)

load_dotenv()


# ---------------------------------------------------------------------------
# LLM initialisation
# ---------------------------------------------------------------------------


def _get_api_key() -> str:
    """Resolve the Groq API key from the environment."""
    try:
        from src.config import get_settings

        key = get_settings().GROQ_API_KEY
        if key:
            return key
    except Exception:
        pass
    return os.getenv("API", os.getenv("GROQ_API_KEY", ""))


def _get_model_name() -> str:
    try:
        from src.config import get_settings

        return get_settings().LLM_MODEL_NAME
    except Exception:
        return "llama-3.1-8b-instant"


@lru_cache()
def get_llm() -> ChatGroq:
    """Return a cached ChatGroq LLM instance."""
    return ChatGroq(
        temperature=0,
        groq_api_key=_get_api_key(),
        model_name=_get_model_name(),
    )


PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
memory = ConversationBufferMemory()


def _get_conversation() -> ConversationChain:
    return ConversationChain(
        llm=get_llm(), memory=memory, verbose=False, prompt=PROMPT
    )


# ---------------------------------------------------------------------------
# Document loading & retrieval
# ---------------------------------------------------------------------------


def load_and_retrieve(file: str):
    """Load a PDF, split, embed, and return a FAISS retriever."""
    logger.info("Loading document: %s", file)
    docs = PyPDFLoader(file).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings()
    vectorstore = FAISS.from_documents(documents=chunks, embedding=embeddings)
    return vectorstore.as_retriever()


def rag_chain(file: str, question: str) -> str:
    """Run RAG pipeline: retrieve context from PDF then answer."""
    retriever = load_and_retrieve(file)
    prompt = ChatPromptTemplate.from_template(document_template)
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | get_llm()
        | StrOutputParser()
    )
    return chain.invoke(question)


def handle_chat(file: Optional[str], question: str) -> str:
    """Route a request to RAG or conversation chain."""
    if file:
        return rag_chain(file, question)
    return _get_conversation().predict(input=question)


# ---------------------------------------------------------------------------
# Async wrappers for FastAPI routes
# ---------------------------------------------------------------------------


async def handle_chat_async(question: str) -> str:
    """Async wrapper around the conversation chain."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, lambda: _get_conversation().predict(input=question)
    )


async def rag_chain_async(file: str, question: str) -> str:
    """Async wrapper around the RAG pipeline."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: rag_chain(file, question))
