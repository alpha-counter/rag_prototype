import os
import re
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from retrieval_service.utils.authUtil import verify_token
from retrieval_service.utils.roleCheckerUtil import RoleChecker

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

allowed_roles = RoleChecker(["admin", "user"])

router = APIRouter(
    tags=["Retrieval"],
    dependencies=[Depends(allowed_roles)]
)

class QueryModel(BaseModel):
    query: str

@lru_cache(maxsize=1)
def _get_retriever():
    vectordb_url = os.getenv("VECTORDB_URL")
    if not vectordb_url:
        raise RuntimeError("VECTORDB_URL is not configured")

    match = re.search(r"[^/]+$", vectordb_url)
    if not match:
        raise RuntimeError("VECTORDB_URL must include a database name")

    collection_name = match.group(0)

    try:
        embeddings = OpenAIEmbeddings()
    except Exception as exc:
        raise RuntimeError(f"Failed to initialise embeddings: {exc}") from exc

    try:
        vectorstore = PGVector(
            embeddings,
            collection_name=collection_name,
            connection=vectordb_url
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to vector store: {exc}") from exc

    return vectorstore.as_retriever(search_kwargs={"k": 3})

@router.post("/retrieve", status_code=200)
async def query_retriever(query_model: QueryModel):
    query = query_model.query
    try:
        retriever = _get_retriever()
        results = retriever.invoke(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
