import os

import pytest

from retrieval_service.routers import retrieval


@pytest.fixture(autouse=True)
def clear_retriever_cache():
    retrieval._get_retriever.cache_clear()
    yield
    retrieval._get_retriever.cache_clear()


def test_get_retriever_requires_vectordb_url(monkeypatch):
    monkeypatch.delenv("VECTORDB_URL", raising=False)

    with pytest.raises(RuntimeError):
        retrieval._get_retriever()


def test_get_retriever_initialises_vector_store(monkeypatch):
    monkeypatch.setenv("VECTORDB_URL", "postgresql+psycopg2://admin:admin@postgres/vector")

    class DummyVector:
        def __init__(self, embeddings, collection_name, connection):
            self.embeddings = embeddings
            self.collection_name = collection_name
            self.connection = connection

        def as_retriever(self, search_kwargs):
            return {"collection": self.collection_name, "kwargs": search_kwargs}

    monkeypatch.setattr(retrieval, "OpenAIEmbeddings", lambda: object())
    monkeypatch.setattr(retrieval, "PGVector", DummyVector)

    retriever_obj = retrieval._get_retriever()

    assert retriever_obj["collection"] == "vector"
    assert retriever_obj["kwargs"] == {"k": 3}
