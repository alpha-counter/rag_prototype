import pytest

from chat_service.state import GraphState
import importlib


web_search = importlib.import_module("chat_service.nodes.web_search")


@pytest.mark.asyncio
async def test_web_search_skips_when_tool_unavailable(monkeypatch):
    monkeypatch.setattr(web_search, "web_search_tool", None)
    state: GraphState = {
        "question": "What is TMF?",
        "generation": "",
        "web_search": True,
        "documents": [],
    }

    result = await web_search.web_search(state)

    assert result["question"] == state["question"]
    assert result["documents"] == []
