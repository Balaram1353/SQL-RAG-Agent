import numpy as np

from app.documents import schema_to_documents
from app.embeddings import create_embedding
from app.schema import get_schema
from functools import lru_cache


def cosine_similarity(a, b):
    """Calculate cosine similarity between two embedding vectors."""
    a = np.asarray(a)
    b = np.asarray(b)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)

@lru_cache(maxsize=1)
def build_index():
    """Build an in-memory index of enriched schema documents."""
    schema = get_schema()
    documents = schema_to_documents(schema)
    index = []

    for document in documents:
        embedding = create_embedding(document["text"])

        index.append({
            "id": document["id"],
            "text": document["text"],
            "embedding": embedding,
        })

    return index


def search(index, query: str, top_k: int = 2):
    """Retrieve the top-k schema documents for a question."""
    if top_k <= 0:
        return []

    query_embedding = create_embedding(query)
    results = []

    for item in index:
        score = cosine_similarity(
            query_embedding,
            item["embedding"],
        )

        results.append({
            "id": item["id"],
            "text": item["text"],
            "score": score,
        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:top_k]


if __name__ == "__main__":
    index = build_index()
    question = "Which customer spent the most money?"

    for result in search(index, question, top_k=4):
        print("=" * 60)
        print(f"Table: {result['id']}")
        print(f"Similarity: {result['score']:.3f}")
        print(result["text"])