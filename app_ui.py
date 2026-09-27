"""DocuMind — Streamlit entry point."""

import streamlit as st

from app.auth import User, authenticate, register_user
from app.exceptions import DocuMindError
from app.ingestion.loaders import load_document
from app.ingestion.splitter import split_documents
from app.ingestion.store import store_document
from app.logging_config import setup_logging
from app.qa.chain import answer_question
from app.qa.history import ConversationHistory

setup_logging()

st.set_page_config(page_title="DocuMind", page_icon="📄", layout="centered")

CUSTOM_CSS = """
<style>
    #MainMenu, footer {visibility: hidden;}

    .block-container {
        max-width: 720px;
        padding-top: 2.5rem;
    }

    .app-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 0;
    }

    .app-subtitle {
        color: #9aa0a6;
        font-size: 0.95rem;
        margin-top: 0.2rem;
        margin-bottom: 1.6rem;
    }

    div[data-testid="stForm"] {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 1.5rem 1.5rem 0.5rem 1.5rem;
    }

    .stButton button, .stFormSubmitButton button {
        border-radius: 8px;
        font-weight: 600;
    }

    .app-footer {
        text-align: center;
        color: #9aa0a6;
        font-size: 0.8rem;
        margin-top: 3rem;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _header() -> None:
    st.markdown('<div class="app-title">📄 DocuMind</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Ask questions and get cited answers '
        "from your own documents.</div>",
        unsafe_allow_html=True,
    )


def _footer() -> None:
    st.markdown(
        '<div class="app-footer">Developed by <b>Fatir Faraz</b></div>',
        unsafe_allow_html=True,
    )


def _login_form() -> None:
    _header()
    login_tab, register_tab = st.tabs(["Log in", "Register"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            try:
                st.session_state.user = authenticate(username, password)
                st.rerun()
            except DocuMindError as exc:
                st.error(exc.user_message)

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username", placeholder="e.g. jane_doe")
            new_password = st.text_input(
                "Choose a password", type="password", placeholder="At least 8 characters"
            )
            reg_submitted = st.form_submit_button("Register", use_container_width=True)
        if reg_submitted:
            try:
                st.session_state.user = register_user(new_username, new_password, role="user")
                st.rerun()
            except DocuMindError as exc:
                st.error(exc.user_message)

    _footer()


def _init_chat_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []  # list of {"role": ..., "content": ..., "sources": [...]}
    if "history" not in st.session_state:
        st.session_state.history = ConversationHistory()


def _render_sources(sources: list) -> None:
    if not sources:
        return
    with st.expander(f"📚 {len(sources)} source(s)"):
        for number, chunk in enumerate(sources, start=1):
            page = chunk.metadata.get("page", "?")
            st.markdown(f"**[{number}]** {chunk.metadata.get('source')}, page {page}")
            st.caption(chunk.content[:200].replace("\n", " ") + "...")


def _upload_page(user: User) -> None:
    st.subheader("Upload a document")
    st.caption("Supported formats: PDF, TXT, MD — up to 10 MB.")

    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "md"])
    if uploaded_file is None:
        return

    if st.button("Ingest document", use_container_width=True):
        raw_bytes = uploaded_file.getvalue()
        with st.spinner("Processing document..."):
            try:
                docs = load_document(uploaded_file.name, raw_bytes)
                chunks = split_documents(docs)
                document_id = store_document(uploaded_file.name, raw_bytes, chunks, user.id)
            except DocuMindError as exc:
                st.error(exc.user_message)
                return
        st.success(f"✅ Stored as document #{document_id} with {len(chunks)} chunks.")


def _main_app(user: User) -> None:
    _init_chat_state()

    with st.sidebar:
        st.markdown(f"**{user.username}**")
        st.caption(user.role.capitalize())
        st.divider()

        page = "Chat"
        if user.role == "admin":
            page = st.radio("Navigate", ["Chat", "Upload"], label_visibility="collapsed")

        st.divider()
        if st.button("Log out", use_container_width=True):
            del st.session_state.user
            st.rerun()
        if page == "Chat" and st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.history = ConversationHistory()
            st.rerun()
        st.markdown(
            '<div class="app-footer">Developed by<br><b>Fatir Faraz</b></div>',
            unsafe_allow_html=True,
        )

    _header()

    if user.role == "admin" and page == "Upload":
        _upload_page(user)
        return

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                _render_sources(message.get("sources", []))

    question = st.chat_input("Ask a question about your documents...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = answer_question(question, st.session_state.history)
                except DocuMindError as exc:
                    st.error(exc.user_message)
                    return
            st.write(answer.text)
            _render_sources(answer.sources)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer.text, "sources": answer.sources}
        )
        st.session_state.history.add(question, answer.text)


def main() -> None:
    if "user" not in st.session_state:
        _login_form()
    else:
        _main_app(st.session_state.user)


main()
