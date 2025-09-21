from typing import Any, Dict

from chat_service.chains.retrieval_grader import retrieval_grader
from chat_service.state import GraphState


async def grade_documents(state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the question
    If any document not a single document is relevant, we will set a flag to run web search

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Filtered out irrelevant documents and updated web_search state
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    
    filtered_docs = []
    web_search = True # Assume we have no relevant documents and need to run web search
    
    for d in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score
        if grade.lower() == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
            web_search = False # We have a relevant document, no need to run web search
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")            
            continue

    return {"documents": filtered_docs, "question": question, "web_search": web_search}