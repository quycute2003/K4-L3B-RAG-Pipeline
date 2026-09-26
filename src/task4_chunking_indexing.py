"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import json
import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from src.contracts import validate_document


load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3").strip()
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"
EMBEDDING_BATCH_SIZE = 32
UPSERT_BATCH_SIZE = 128


@lru_cache(maxsize=4)
def _get_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _validate_vectors(
    vectors: list[list[float]], expected_count: int
) -> list[list[float]]:
    if len(vectors) != expected_count:
        raise ValueError(
            f"Embedding provider returned {len(vectors)} vectors for "
            f"{expected_count} texts"
        )
    if not vectors:
        return vectors

    dimension = len(vectors[0])
    if dimension <= 0 or any(len(vector) != dimension for vector in vectors):
        raise ValueError("Embedding vectors must have one consistent dimension")
    return [[float(value) for value in vector] for vector in vectors]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts with the single provider configured in ``.env``."""
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("Every text to embed must be a non-empty string")

    provider = EMBEDDING_PROVIDER.lower()
    if provider == "sentence_transformers":
        model = _get_sentence_transformer(EMBEDDING_MODEL)
        vectors = model.encode(
            texts,
            batch_size=EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
    elif provider == "openai":
        from openai import OpenAI

        response = OpenAI().embeddings.create(model=EMBEDDING_MODEL, input=texts)
        vectors = [item.embedding for item in response.data]
    elif provider == "gemini":
        from google import genai

        response = genai.Client().models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
        )
        vectors = [embedding.values for embedding in response.embeddings]
    else:
        raise ValueError(
            "Unsupported EMBEDDING_PROVIDER. Use sentence_transformers, "
            "openai or gemini."
        )

    return _validate_vectors(vectors, len(texts))


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    expected_metadata = {
        "hnsw:space": "cosine",
        "embedding_provider": EMBEDDING_PROVIDER,
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata=expected_metadata,
    )
    actual_metadata = collection.metadata or {}
    mismatches = {
        key: (actual_metadata.get(key), expected)
        for key, expected in expected_metadata.items()
        if actual_metadata.get(key) != expected
    }
    if mismatches:
        raise ValueError(
            "Existing Chroma collection configuration does not match Task 4: "
            f"{mismatches}. Rebuild the local index."
        )
    return collection


def _parse_front_matter(markdown: str) -> tuple[dict, str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, markdown.strip()

    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        return {}, markdown.strip()

    metadata = {}
    for line in lines[1:closing_index]:
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        raw_value = raw_value.strip()
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value.strip("\"'")
        metadata[key.strip()] = value

    return metadata, "\n".join(lines[closing_index + 1 :]).strip()


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        relative_path = path.relative_to(STANDARDIZED_DIR)
        doc_type = relative_path.parts[0] if relative_path.parts else ""
        if doc_type not in {"legal", "news"}:
            continue

        front_matter, content = _parse_front_matter(
            path.read_text(encoding="utf-8")
        )
        source = str(front_matter.get("source") or path.name).strip()
        title = str(
            front_matter.get("title") or path.stem.replace("_", " ").title()
        ).strip()
        raw_url = front_matter.get("url", source if source.startswith("http") else None)
        url = str(raw_url).strip() if raw_url is not None else None
        document = {
            "id": relative_path.with_suffix("").as_posix(),
            "content": content,
            "metadata": {
                "source": source,
                "title": title,
                "doc_type": doc_type,
                "url": url,
            },
        }
        validate_document(document)
        documents.append(document)

    if not documents:
        raise ValueError(f"No standardized Markdown found in {STANDARDIZED_DIR}")
    ids = [document["id"] for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("Document IDs must be unique")
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    if CHUNK_OVERLAP >= CHUNK_SIZE:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    seen_document_ids = set()
    for document in documents:
        validate_document(document)
        if document["id"] in seen_document_ids:
            raise ValueError(f"Duplicate document ID: {document['id']}")
        seen_document_ids.add(document["id"])

        texts = [text.strip() for text in splitter.split_text(document["content"])]
        texts = [text for text in texts if re.search(r"\w", text, flags=re.UNICODE)]
        for index, text in enumerate(texts):
            chunk = {
                "id": f"{document['id']}::chunk-{index:04d}",
                "content": text,
                "metadata": {**document["metadata"], "chunk_index": index},
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)

    ids = [chunk["id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Chunk IDs must be unique")
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []
    for chunk in chunks:
        validate_document(chunk, require_chunk=True)

    vectors = []
    total = len(chunks)
    for start in range(0, total, EMBEDDING_BATCH_SIZE):
        batch = chunks[start : start + EMBEDDING_BATCH_SIZE]
        vectors.extend(embed_texts([chunk["content"] for chunk in batch]))
        current = min(start + EMBEDDING_BATCH_SIZE, total)
        print(f"Embedding progress: {current}/{total} chunks ({current * 100 // total}%)", flush=True)

    _validate_vectors(vectors, len(chunks))
    return [
        {**chunk, "embedding": vector}
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        raise ValueError("Cannot index an empty chunk list")

    ids = [chunk["id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Cannot index duplicate chunk IDs")

    dimension = None
    for chunk in chunks:
        validate_document(chunk, require_chunk=True)
        vector = chunk.get("embedding")
        if not isinstance(vector, list) or not vector:
            raise ValueError(f"Chunk has no embedding: {chunk['id']}")
        if dimension is None:
            dimension = len(vector)
        elif len(vector) != dimension:
            raise ValueError("All chunk embeddings must have the same dimension")

    collection = get_collection()
    existing_ids = set(collection.get(include=[])["ids"])
    stale_ids = sorted(existing_ids - set(ids))
    if stale_ids:
        collection.delete(ids=stale_ids)

    for start in range(0, len(chunks), UPSERT_BATCH_SIZE):
        batch = chunks[start : start + UPSERT_BATCH_SIZE]
        metadatas = []
        for chunk in batch:
            metadata = dict(chunk["metadata"])
            metadata["url"] = metadata.get("url") or ""
            metadatas.append(metadata)
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=metadatas,
        )
        print(f"Upserted to ChromaDB: {min(start + UPSERT_BATCH_SIZE, len(chunks))}/{len(chunks)} chunks", flush=True)


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    collection = get_collection()
    print(
        f"Indexed {len(embedded_chunks)} chunks from {len(documents)} documents "
        f"(collection count: {collection.count()})"
    )


if __name__ == "__main__":
    run_pipeline()
