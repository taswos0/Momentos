"""
Vector Service — converts text and images into embeddings and stores/queries Qdrant.

The semantic magic: both text paragraphs and images are embedded into the same
vector space. Cosine similarity then automatically finds which image belongs with
which paragraph — no human curation needed.
"""
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import settings
import uuid

_openai = AsyncOpenAI(api_key=settings.openai_api_key)
_qdrant = AsyncQdrantClient(url=settings.qdrant_url)

COLLECTION_NAME = "alchemist_assets"
VECTOR_SIZE = 1536  # text-embedding-3-small dimension


async def ensure_collection() -> None:
    """Creates the Qdrant collection if it doesn't exist yet."""
    collections = await _qdrant.get_collections()
    names = [c.name for c in collections.collections]
    if COLLECTION_NAME not in names:
        await _qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


async def embed_texts(texts: list[str], job_id: str) -> list[str]:
    """
    Embeds a list of text blocks and upserts them into Qdrant.
    Returns a list of the generated point IDs.
    """
    await ensure_collection()

    response = await _openai.embeddings.create(
        input=texts,
        model="text-embedding-3-small",
    )

    points = []
    ids = []
    for text, embedding_data in zip(texts, response.data):
        point_id = str(uuid.uuid4())
        ids.append(point_id)
        points.append(
            PointStruct(
                id=point_id,
                vector=embedding_data.embedding,
                payload={"job_id": job_id, "type": "text", "content": text},
            )
        )

    await _qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return ids


async def find_best_image_for_paragraph(paragraph: str, job_id: str) -> str | None:
    """
    Embeds a paragraph and searches Qdrant for the most semantically similar
    image asset stored for the same job. Returns the local file path or None.
    """
    response = await _openai.embeddings.create(
        input=[paragraph],
        model="text-embedding-3-small",
    )
    query_vector = response.data[0].embedding

    results = await _qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter={
            "must": [
                {"key": "job_id", "match": {"value": job_id}},
                {"key": "type",   "match": {"value": "image"}},
            ]
        },
        limit=1,
        score_threshold=0.70,  # Only match if similarity is high enough
    )

    if results:
        return results[0].payload.get("local_path")
    return None
