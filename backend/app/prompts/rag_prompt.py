"""
RAG prompt templates.

Engineered prompts for question answering from context.
"""


def build_rag_prompt(question: str, context: str) -> str:
    """
    Build RAG prompt for question answering.

    Combines question with retrieved context to guide LLM generation.

    Args:
        question: User question
        context: Retrieved context from documents

    Returns:
        Formatted prompt for LLM
    """
    prompt = f"""You are a helpful assistant that answers questions based on provided context.

Answer the following question based ONLY on the provided context. If the answer cannot be found in the context, explicitly state that you cannot answer the question.

<CONTEXT>
{context}
</CONTEXT>

<QUESTION>
{question}
</QUESTION>

<INSTRUCTIONS>
- Answer only using information from the context
- Be concise and direct
- If uncertain, indicate your confidence level
- Never make up information not in the context
</INSTRUCTIONS>

Answer:"""

    return prompt


def build_sufficiency_check_prompt(question: str, context: str) -> str:
    """
    Build prompt to check if context is sufficient.

    Uses LLM to validate retrieved context can answer the question.

    Args:
        question: User question
        context: Retrieved context

    Returns:
        Formatted prompt for sufficiency check
    """
    prompt = f"""Determine if the following context contains enough information to answer the question.

<CONTEXT>
{context}
</CONTEXT>

<QUESTION>
{question}
</QUESTION>

Respond with exactly one word: "SUFFICIENT" or "INSUFFICIENT"

Answer:"""

    return prompt
