"""Streamlit chatbot for the Huế heritage and tourism corpus."""

from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(page_title="Tra cứu di sản Huế", page_icon="🏯", layout="wide")


def render_sources(sources: list[dict], retrieval_source: str, message_index: int) -> None:
    if not sources:
        return
    st.caption(f"Nguồn truy xuất: {retrieval_source}")
    with st.expander(f"Nguồn đã dùng ({len(sources)})", expanded=True):
        for number, item in enumerate(sources, 1):
            metadata = item["metadata"]
            st.markdown(f"**[{number}] {metadata['title']}**")
            url = metadata.get("url") or metadata.get("source")
            if isinstance(url, str) and urlparse(url).scheme in {"http", "https"}:
                st.link_button(f"Mở nguồn {message_index + 1}.{number}", url)
            else:
                st.caption(f"Nguồn: {metadata['source']}")
            detail = (
                f"ID: `{item['id']}` · Cách tìm: {item['retrieval_method']} "
                f"· Điểm: {item['score']:.4f}"
            )
            if metadata.get("page_index") is not None:
                detail += f" · Trang: {metadata['page_index']}"
            st.caption(detail)


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("Tra cứu di sản Huế")
    st.caption("Câu trả lời dựa trên tài liệu văn hóa và du lịch Huế của nhóm DeltaX.")
    top_k = st.slider("Số đoạn tài liệu", min_value=1, max_value=10, value=5)

st.title("Chatbot tra cứu di sản Huế")
st.caption("Hỏi về Quần thể Di tích Cố đô Huế, Nhã nhạc, Ca Huế và các tài liệu du lịch liên quan.")

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(
                message.get("sources", []),
                message.get("retrieval_source", "none"),
                index,
            )

query = st.chat_input("Nhập câu hỏi về di sản hoặc du lịch Huế...")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm tài liệu và tạo câu trả lời..."):
            result = generate_with_citation(query, top_k=top_k)
        st.markdown(result["answer"])
        render_sources(result["sources"], result["retrieval_source"], len(st.session_state.messages))

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "retrieval_source": result["retrieval_source"],
        }
    )
