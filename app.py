# app.py

import streamlit as st
from rag import process_pdf, create_vectorstore, create_retriever, get_answer

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="Chat with PDF",
    page_icon="📄",
    layout="wide"
)

# -------------------------------
# Custom Styling (ChatGPT-like)
# -------------------------------
st.markdown("""
<style>
body {
    background-color: #0E1117;
}
.stChatMessage {
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
}
.stChatMessage.user {
    background-color: #1E293B;
}
.stChatMessage.assistant {
    background-color: #111827;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Title
# -------------------------------
st.title("📄 PDF AI Paglu 🤗")
st.caption("Upload a PDF and chat like Person")

# -------------------------------
# Session State
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "retriever" not in st.session_state:
    st.session_state.retriever = None

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.header("📂 Upload PDF")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        if st.session_state.retriever is None:
            with st.spinner("Processing PDF... ⏳"):
                chunks = process_pdf(uploaded_file)
                vectorstore = create_vectorstore(chunks)
                retriever = create_retriever(vectorstore)

                st.session_state.retriever = retriever

            st.success("✅ PDF ready! You can chat now.")

    # Reset button
    if st.button("🔄 Reset Chat"):
        st.session_state.chat_history = []

# -------------------------------
# Display Chat History FIRST
# -------------------------------
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

# -------------------------------
# Chat Input
# -------------------------------
query = st.chat_input("Ask something about your PDF...")

if query and st.session_state.retriever:

    # Save user message
    st.session_state.chat_history.append(("user", query))

    # Show thinking animation
    with st.spinner("Thinking... 🤔"):
        answer = get_answer(st.session_state.retriever, query)

    # Save assistant response
    st.session_state.chat_history.append(("assistant", answer))

    # Rerun to update UI cleanly
    st.rerun()