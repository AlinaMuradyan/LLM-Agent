from typing import Dict, List, Tuple

import numpy as np
import faiss
import tiktoken
from openai import OpenAI

from config import OPENAI_API_KEY


"""
Modern, ChatGPT-style memory for the QA chatbot.

Key ideas:
- Short-term memory: token-bounded sliding window of recent messages per chat_id.
- Long-term memory: semantic Q&A store using embeddings + vector similarity.
- Explicit prompt construction: system + recent chat + relevant Q&A + current question.
"""


# ------------ OpenAI client & models ------------

MODEL_NAME = "gpt-4.1-nano"
EMBEDDING_MODEL = "text-embedding-3-small"

client = OpenAI(api_key=OPENAI_API_KEY)
encoding = tiktoken.encoding_for_model(MODEL_NAME)

# Total context for history + semantic Q&A (leave headroom for system + question)
MAX_HISTORY_TOKENS = 1200
MAX_VECTOR_QA_TOKENS = 800


# ------------ In-memory stores ------------

# ------------ In-memory stores ------------

# Long-term semantic memory still uses FAISS for now
import database

class FaissQAVectorStore:
# ... (rest of FaissQAVectorStore remains same)
    def __init__(self) -> None:
        self._questions: List[str] = []
        self._answers: List[str] = []
        self._index: faiss.IndexFlatIP | None = None
        self._dim: int | None = None

    def add(self, question: str, answer: str, embedding: np.ndarray) -> None:
        emb = embedding.astype("float32")

        # Lazily initialize index with embedding dimension
        if self._index is None:
            self._dim = emb.shape[0]
            self._index = faiss.IndexFlatIP(self._dim)

        # Normalize for cosine similarity
        faiss.normalize_L2(emb.reshape(1, -1))
        self._index.add(emb.reshape(1, -1))

        self._questions.append(question)
        self._answers.append(answer)

    def is_empty(self) -> bool:
        return self._index is None or self._index.ntotal == 0

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, str]]:
        if self.is_empty():
            return []

        q = query_embedding.astype("float32").reshape(1, -1)
        faiss.normalize_L2(q)

        k = min(top_k, self._index.ntotal)
        _, indices = self._index.search(q, k)

        results: List[Tuple[str, str]] = []
        for idx in indices[0]:
            q_text = self._questions[int(idx)]
            a_text = self._answers[int(idx)]
            results.append((q_text, a_text))
        return results


vector_store = FaissQAVectorStore()


# ------------ Token utilities ------------

def count_tokens(text: str) -> int:
    """Count tokens for a single text segment using the model's tokenizer."""
    return len(encoding.encode(text))


def count_message_list_tokens(messages: List[Dict[str, str]]) -> int:
    """
    Approximate token count for a list of messages.
    We concatenate role + content for a rough, model-aware estimate.
    """
    total = 0
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        total += count_tokens(f"{role}: {content}\n")
    return total


def select_recent_messages_within_budget(
    history: List[Dict[str, str]],
    max_tokens: int,
) -> List[Dict[str, str]]:
    """
    Take the most recent messages, trimming from the oldest first,
    until the token budget is reached.
    """
    selected: List[Dict[str, str]] = []
    total_tokens = 0

    # Traverse history from newest to oldest, then reverse at the end
    for msg in reversed(history):
        msg_tokens = count_message_list_tokens([msg])
        if total_tokens + msg_tokens > max_tokens:
            break
        # Create a clean copy with only role and content for OpenAI
        clean_msg = {"role": msg["role"], "content": msg["content"]}
        selected.append(clean_msg)
        total_tokens += msg_tokens

    return list(reversed(selected))


def select_vector_qa_within_budget(
    qa_pairs: List[Tuple[str, str]],
    max_tokens: int,
) -> List[Tuple[str, str]]:
    """
    Trim retrieved Q&A pairs so their combined token cost stays within max_tokens.
    """
    selected: List[Tuple[str, str]] = []
    total_tokens = 0

    for q, a in qa_pairs:
        # Rough count for "Q: ... A: ..." format
        pair_text = f"Q: {q}\nA: {a}\n"
        pair_tokens = count_tokens(pair_text)
        if total_tokens + pair_tokens > max_tokens:
            break
        selected.append((q, a))
        total_tokens += pair_tokens

    return selected


# ------------ Embeddings & heuristics ------------

def embed_text(text: str) -> np.ndarray:
    """Create an embedding vector for the given text."""
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return np.array(resp.data[0].embedding, dtype="float32")


def should_store_in_vector_memory(question: str, answer: str) -> bool:
    """
    Heuristic: only store exchanges with long-term informational value.

    We skip:
    - Very short questions or answers
    - Obvious greetings / small talk
    """
    q_lower = question.strip().lower()

    # Simple small-talk / greeting detection
    small_talk_prefixes = (
        "hi", "hello", "hey", "good morning", "good evening",
        "thanks", "thank you", "ok", "okay", "bye", "goodbye",
    )
    if any(q_lower.startswith(p) for p in small_talk_prefixes):
        return False

    # Very short content is unlikely to be a reusable Q&A
    if len(question.split()) < 4 or len(answer.split()) < 6:
        return False

    return True


# ------------ Core QA logic ------------

SYSTEM_INSTRUCTION = (
    "You are a concise, helpful QA assistant. "
    "Answer the user's question clearly and accurately. "
    "If you are unsure, say that you don't know."
)


def get_chat_history(conversation_id: str) -> List[Dict[str, str]]:
    return database.get_messages(conversation_id)


def build_vector_memory_context(question: str) -> List[Tuple[str, str]]:
    """
    Retrieve top-K semantically similar past Q&A from the vector store.
    These are used as optional context, not as conversation history.
    """
    if vector_store.is_empty():
        return []

    query_emb = embed_text(question)
    retrieved = vector_store.search(query_emb, top_k=5)
    return select_vector_qa_within_budget(retrieved, MAX_VECTOR_QA_TOKENS)


def build_messages_for_model(
    conversation_id: str,
    question: str,
) -> List[Dict[str, str]]:
    """
    Construct the full message list for the model:
    - System instruction
    - Recent short-term chat history (token-trimmed)
    - Relevant past Q&A (vector retrieval) as optional system context
    - Current user question
    """
    history = get_chat_history(conversation_id)

    # 1) System message
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_INSTRUCTION}
    ]

    # 2) Relevant semantic Q&A (episodic recall)
    qa_context = build_vector_memory_context(question)
    if qa_context:
        qa_text_lines = ["Here are some relevant previous Q&A you have given:"]
        for idx, (q, a) in enumerate(qa_context, start=1):
            qa_text_lines.append(f"Q{idx}: {q}")
            qa_text_lines.append(f"A{idx}: {a}")
            qa_text_lines.append("")  # blank line between entries
        messages.append(
            {
                "role": "system",
                "content": "\n".join(qa_text_lines).strip(),
            }
        )

    # 3) Short-term conversational history (sliding window)
    recent_history = select_recent_messages_within_budget(
        history,
        MAX_HISTORY_TOKENS,
    )
    messages.extend(recent_history)

    # 4) Current question as the latest user message
    messages.append({"role": "user", "content": question})

    return messages


def call_model(messages: List[Dict[str, str]]) -> str:
    """Call the chat model with the constructed messages and return the answer text."""
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


def update_memories_after_response(
    conversation_id: str,
    question: str,
    answer: str,
) -> None:
    """
    After each response:
    - Save to MySQL database (short-term history).
    - Optionally store Q&A in semantic vector memory (FAISS).
    """
    # Short-term: save to database
    database.add_message(conversation_id, 'user', question)
    database.add_message(conversation_id, 'assistant', answer)

    # Long-term semantic memory (vector store)
    if should_store_in_vector_memory(question, answer):
        q_emb = embed_text(question)
        vector_store.add(question, answer, q_emb)


def ask_question(question: str, conversation_id: str) -> str:
    """
    Main entry point used by FastAPI.

    Implements:
    - Token-bounded short-term memory (sliding window)
    - Long-term semantic Q&A (vector store)
    - Explicit prompt construction
    """
    messages = build_messages_for_model(conversation_id=conversation_id, question=question)
    answer = call_model(messages)
    update_memories_after_response(conversation_id=conversation_id, question=question, answer=answer)
    return answer
