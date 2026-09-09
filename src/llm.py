import os
from typing import Any

from groq import Groq

SYSTEM_PROMPT = """You are an enterprise knowledge assistant.
Answer only from the supplied context.
If the context does not contain enough information, say you do not have enough authorized information.
Never invent confidential facts or bypass access controls.
Cite the source filenames in your answer when available."""


def answer(question: str, contexts: list[dict[str, Any]]) -> str:
    if not contexts:
        return "I couldn't find any authorized documents relevant to your question."

    context = "\n\n".join(
        f"[Source: {item.get('source', 'unknown')}]\n{item.get('text', '')}"
        for item in contexts
    )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Authorized context:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    return response.choices[0].message.content or "No answer was generated."
