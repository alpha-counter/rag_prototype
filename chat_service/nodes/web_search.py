from typing import Any, Dict

import logging
from typing import Optional

from dotenv import load_dotenv
from langchain.schema import Document
from langchain_community.tools.tavily_search import TavilySearchResults

from chat_service.state import GraphState

logger = logging.getLogger(__name__)

load_dotenv()


def _init_tool() -> Optional[TavilySearchResults]:
    try:
        return TavilySearchResults(k=3)
    except Exception as exc:
        logger.warning("Web search disabled: %s", exc)
        return None


web_search_tool = _init_tool()


async def web_search(state: GraphState) -> Dict[str, Any]:
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state["documents"]

    if web_search_tool is None:
        logger.info("Skipping web search; tool is not configured.")
        return {"documents": documents or [], "question": question}

    docs = web_search_tool.invoke({"query": question})
    web_results = "\n".join([d["content"] for d in docs])
    web_results = Document(page_content=web_results)
    if documents is not None:
        documents.append(web_results)
    else:
        documents = [web_results]
    return {"documents": documents, "question": question}
