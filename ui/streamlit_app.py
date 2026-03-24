import os
from typing import Any, Dict, List
import requests
import streamlit as st

from govassist.config import load_env_file

load_env_file()


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip()
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
SESSION_ENDPOINT = f"{API_BASE_URL}/sessions"


def fetch_chat_response(query: str, top_k: int, session_id: str | None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "query": query,
        "top_k": top_k,
    }
    if session_id:
        payload["session_id"] = session_id

    response = requests.post(CHAT_ENDPOINT, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def fetch_session_history(session_id: str) -> List[Dict[str, Any]]:
    response = requests.get(f"{SESSION_ENDPOINT}/{session_id}", timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("history", [])


def render_matches(matches: List[Dict[str, Any]]) -> None:
    if not matches:
        return

    with st.expander("Relevant Schemes"):
        for match in matches:
            st.markdown(f"**{match.get('scheme_name', 'Unknown Scheme')}**")
            st.write(f"Category: {match.get('category', 'N/A')}")
            score = match.get("score", 0) or 0
            st.write(f"Score: {round(float(score), 3)}")
            if match.get("official_link"):
                st.markdown(f"[Official Link]({match['official_link']})")
            st.divider()


def activate_archived_chat(chat: Dict[str, Any]) -> None:
    st.session_state.messages = chat.get("messages", []).copy()
    st.session_state.session_id = chat.get("session_id")


def build_chat_label(chat: Dict[str, Any], index: int) -> str:
    messages = chat.get("messages", [])
    first_user_message = next(
        (message.get("content", "").strip() for message in messages if message.get("role") == "user"),
        "",
    )
    preview = first_user_message[:30].strip()
    if len(first_user_message) > 30:
        preview += "..."
    if not preview:
        preview = "New chat"
    return f"Chat {index} - {preview}"


def archive_current_chat() -> None:
    if not st.session_state.messages:
        return

    chat_snapshot = {
        "session_id": st.session_state.session_id,
        "messages": st.session_state.messages.copy(),
    }

    current_session_id = chat_snapshot.get("session_id")
    if current_session_id:
        for index, archived_chat in enumerate(st.session_state.archived_chats):
            if archived_chat.get("session_id") == current_session_id:
                st.session_state.archived_chats[index] = chat_snapshot
                return

    if chat_snapshot not in st.session_state.archived_chats:
        st.session_state.archived_chats.append(chat_snapshot)


def render_app() -> None:
    st.set_page_config(
        page_title="Government Schemes Assistant",
        page_icon="🏛️",
        layout="wide",
    )

    st.title("Government Schemes Assistant")
    st.caption("A Streamlit chatbot powered by FastAPI, Qdrant, BGE embeddings, and Groq.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "archived_chats" not in st.session_state:
        st.session_state.archived_chats = []

    with st.sidebar:
        st.header("Settings")
        api_url = st.text_input("FastAPI URL", value=API_BASE_URL).strip() or DEFAULT_API_BASE_URL
        top_k = st.slider("Top K Schemes", min_value=1, max_value=5, value=3)

        if st.button("Start New Chat"):
            archive_current_chat()
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()

        if st.session_state.archived_chats:
            st.markdown("### Previous Chats")
            for index, chat in enumerate(st.session_state.archived_chats, start=1):
                if st.button(
                    build_chat_label(chat, index),
                    key=f"open_archived_chat_{index}",
                    use_container_width=True,
                ):
                    activate_archived_chat(chat)
                    st.rerun()

        if st.session_state.session_id:
            st.write(f"Session ID: `{st.session_state.session_id}`")
            if st.button("Reload Saved History"):
                try:
                    history = fetch_session_history(st.session_state.session_id)
                    st.session_state.messages = []
                    for turn in history:
                        st.session_state.messages.append(
                            {
                                "role": "user",
                                "content": turn.get("user", ""),
                            }
                        )
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": turn.get("assistant", ""),
                                "matches": turn.get("matches", []),
                            }
                        )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not load history: {exc}")

    global CHAT_ENDPOINT, SESSION_ENDPOINT
    CHAT_ENDPOINT = f"{api_url.rstrip('/')}/chat"
    SESSION_ENDPOINT = f"{api_url.rstrip('/')}/sessions"

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_matches(message.get("matches", []))

    user_query = st.chat_input("Ask about scholarships, farmers, loans, pensions, women schemes...")

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})

        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Finding relevant schemes..."):
                try:
                    result = fetch_chat_response(
                        query=user_query,
                        top_k=top_k,
                        session_id=st.session_state.session_id,
                    )

                    st.session_state.session_id = result.get("session_id")
                    answer = str(result.get("answer", "No answer returned."))
                    matches = result.get("matches", []) or []

                    st.markdown(answer)
                    render_matches(matches)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "matches": matches,
                        }
                    )
                    archive_current_chat()
                except requests.HTTPError as exc:
                    error_text = exc.response.text if exc.response is not None else str(exc)
                    st.error(f"API error: {error_text}")
                except requests.ConnectionError:
                    st.error(
                        "Could not reach the FastAPI backend. Start it with "
                        "`uvicorn main:app --host 127.0.0.1 --port 8000` "
                        "or update the FastAPI URL in the sidebar."
                    )
                except Exception as exc:
                    st.error(f"Something went wrong: {exc}")
