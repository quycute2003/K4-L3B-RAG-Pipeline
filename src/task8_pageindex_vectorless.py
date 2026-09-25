"""Optional PageIndex cloud retrieval over the same public corpus.

Run this module once to upload PDFs. The cache stores document IDs, never keys.
PageIndex accepts PDFs, so news Markdown is rendered to temporary PDFs.
"""

import hashlib
import html
import json
import os
import time
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FutureTimeout,
    as_completed,
)
from pathlib import Path

from dotenv import load_dotenv

from .task4_chunking_indexing import load_documents


load_dotenv()

ROOT = Path(__file__).parent.parent
STANDARDIZED_DIR = ROOT / "data" / "standardized"
LEGAL_DIR = ROOT / "data" / "landing" / "legal"
PDF_DIR = ROOT / "pageindex_pdfs"
CACHE_PATH = ROOT / "pageindex_doc_ids.json"
CALL_TIMEOUT = 20.0
QUERY_TIMEOUT = 30.0
UPLOAD_TIMEOUT = 180.0


def _client():
    key = os.getenv("PAGEINDEX_API_KEY", "").strip()
    if not key:
        return None
    from pageindex import PageIndexClient

    return PageIndexClient(api_key=key)


def _call(fn, *args, timeout: float = CALL_TIMEOUT, **kwargs):
    """Bound a synchronous SDK call without waiting for a timed-out worker."""
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        return pool.submit(fn, *args, **kwargs).result(timeout=timeout)
    except FutureTimeout as exc:
        raise TimeoutError("PageIndex request timed out") from exc
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _read_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("PageIndex cache must be a JSON object")
    return data


def _write_cache(cache: dict) -> None:
    temporary = CACHE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(CACHE_PATH)


def _news_pdf(document: dict) -> Path:
    """Render UTF-8 article text with Chromium's Vietnamese-capable fonts."""
    target = PDF_DIR / f"{Path(document['id']).name}.pdf"
    text = html.escape(document["content"])
    title = html.escape(document["metadata"]["title"])
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content(
                "<html><meta charset='utf-8'><style>"
                "body{font-family:Arial,sans-serif;line-height:1.45}"
                "pre{white-space:pre-wrap;font:inherit}</style>"
                f"<h1>{title}</h1><pre>{text}</pre></html>"
            )
            page.pdf(path=str(target), format="A4", print_background=True)
        finally:
            browser.close()
    return target


def _pdf_for(document: dict) -> Path:
    if document["metadata"]["doc_type"] == "news":
        return _news_pdf(document)
    pdf = LEGAL_DIR / f"{Path(document['id']).name}.pdf"
    if not pdf.is_file():
        raise FileNotFoundError(f"Missing legal PDF for {document['id']}: {pdf}")
    return pdf


def _ready(client, doc_id: str) -> bool:
    deadline = time.monotonic() + UPLOAD_TIMEOUT
    while time.monotonic() < deadline:
        status = _call(client.get_document, doc_id, timeout=CALL_TIMEOUT).get("status")
        if status == "completed":
            return True
        if status == "failed":
            return False
        time.sleep(2)
    return False


def upload_documents() -> None:
    """Upload changed public documents and cache their PageIndex IDs."""
    client = _client()
    if client is None:
        raise ValueError("Set PAGEINDEX_API_KEY in .env to upload PageIndex documents")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    cache = _read_cache()
    for document in load_documents():
        identifier = document["id"]
        fingerprint = hashlib.sha256(document["content"].encode("utf-8")).hexdigest()
        existing = cache.get(identifier)
        if existing and existing.get("fingerprint") == fingerprint:
            if _ready(client, existing["doc_id"]):
                continue
        pdf = _pdf_for(document)
        response = _call(client.submit_document, str(pdf), timeout=CALL_TIMEOUT)
        doc_id = response["doc_id"]
        cache[identifier] = {
            "doc_id": doc_id,
            "fingerprint": fingerprint,
            "metadata": document["metadata"],
        }
        _write_cache(cache)
        if not _ready(client, doc_id):
            raise TimeoutError(f"PageIndex document not ready: {identifier} ({doc_id})")


def _retrieval(client, doc_id: str, query: str, deadline: float) -> dict:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("PageIndex search timed out")
    submission = _call(client.submit_query, doc_id, query, timeout=min(CALL_TIMEOUT, remaining))
    retrieval_id = submission["retrieval_id"]
    while time.monotonic() < deadline:
        response = _call(
            client.get_retrieval,
            retrieval_id,
            timeout=min(CALL_TIMEOUT, deadline - time.monotonic()),
        )
        status = response.get("status")
        if status == "completed":
            return response
        if status == "failed":
            return {}
        time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
    raise TimeoutError("PageIndex search timed out")


def _content_items(node: dict):
    blocks = node.get("relevant_contents") or []
    for block in blocks:
        if isinstance(block, dict):
            yield block
        elif isinstance(block, list):
            for item in block:
                if isinstance(item, dict):
                    yield item
    if not blocks and node.get("text"):
        yield {"relevant_content": node["text"], "page_index": node.get("page_index")}


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Return ranked, source-labelled passages from cached PageIndex PDFs."""
    if not query.strip() or top_k <= 0:
        return []
    client = _client()
    if client is None:
        return []
    cache = _read_cache()
    if not cache:
        return []

    deadline = time.monotonic() + QUERY_TIMEOUT
    entries = list(cache.values())
    pool = ThreadPoolExecutor(max_workers=min(4, len(entries)))
    responses = {}
    try:
        futures = {
            pool.submit(_retrieval, _client(), entry["doc_id"], query, deadline): index
            for index, entry in enumerate(entries)
        }
        try:
            for future in as_completed(futures, timeout=QUERY_TIMEOUT):
                try:
                    responses[futures[future]] = future.result()
                except Exception:
                    pass
        except FutureTimeout:
            pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

    results = []
    seen = set()
    for index, entry in enumerate(entries):
        response = responses.get(index, {})
        local_rank = 0
        for node in response.get("retrieved_nodes") or []:
            if not isinstance(node, dict):
                continue
            for block in _content_items(node):
                content = str(block.get("relevant_content") or "").strip()
                if not content:
                    continue
                digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
                item_id = f"pageindex::{entry['doc_id']}::{node.get('node_id', '')}::{digest}"
                if item_id in seen:
                    continue
                seen.add(item_id)
                local_rank += 1
                metadata = dict(entry["metadata"])
                page_index = block.get("page_index")
                metadata["chunk_index"] = (
                    max(page_index - 1, 0)
                    if isinstance(page_index, int) and not isinstance(page_index, bool)
                    else 0
                )
                if page_index is not None:
                    metadata["page_index"] = page_index
                results.append(
                    {
                        "id": item_id,
                        "content": content,
                        "score": 1.0 / local_rank,
                        "metadata": metadata,
                        "retrieval_method": "pageindex",
                    }
                )
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    upload_documents()
