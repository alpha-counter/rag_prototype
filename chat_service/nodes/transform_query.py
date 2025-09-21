from typing import Any, Dict

from chat_service.chains.question_rewriter import question_rewriter
from chat_service.state import GraphState

async def transform_query(state: GraphState) -> Dict[str, Any]:
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]

    # Re-write question
    better_question = question_rewriter.invoke({"question": question})
    return {"documents": documents, "question": better_question}