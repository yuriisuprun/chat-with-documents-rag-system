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

Please answer the following question. Use the provided context if relevant, but you may also draw on general knowledge if the specific answer isn't in the context. Always indicate the source when quoting from the context.

<CONTEXT>
{context}
</CONTEXT>

<QUESTION>
{question}
</QUESTION>

<INSTRUCTIONS>
- If information is in the context, cite it with page numbers
- If you cannot find specific information, clearly state what you don't know from the context
- Provide helpful information based on what you can find or infer
- Be concise and direct
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
    prompt = f"""You will determine if the following context contains enough information to answer the question.

Context:
{context}

Question:
{question}

Can this context answer the question above? 
Reply with ONLY the word "SUFFICIENT" if yes, or "INSUFFICIENT" if no. Do not include any other text.

Answer: """

    return prompt
