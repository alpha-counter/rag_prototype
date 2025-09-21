import os
from typing import Any, Dict

import httpx
from chat_service.state import GraphState
from dotenv import load_dotenv
from langchain.schema import Document

load_dotenv()


RETRIEVAL_SERVICE_URL = os.getenv("RETRIEVAL_SERVICE_URL", "http://retrieval_service:8003").rstrip("/")


async def query_retriever(query: str):
    payload = {"query": query}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{RETRIEVAL_SERVICE_URL}/retrieve",
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Retrieval service error: {exc}") from exc

    return response.json()


async def retrieve(state: GraphState) -> Dict[str, Any]:
    print("---RETRIEVE---")
    question = state["question"]

    documents = await query_retriever(question)

    # Convert dictionaries to Document objects
    documents_obj = [Document(page_content=d['page_content'], metadata=d['metadata']) for d in documents]

    return {"documents": documents_obj, "question": question}
