# rag.py

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from dotenv import load_dotenv
import tempfile
import os

load_dotenv()

# -------------------------------
# LLM
# -------------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# -------------------------------
# Process PDF (for Streamlit upload)
# -------------------------------
def process_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    return splitter.split_documents(docs)

# -------------------------------
# Embeddings
# -------------------------------
def get_embedding():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# -------------------------------
# Vector Store
# -------------------------------
def create_vectorstore(chunks):
    embeddings = get_embedding()
    return FAISS.from_documents(chunks, embeddings)

# -------------------------------
# Retriever
# -------------------------------
def create_retriever(vectorstore):
    base_retriever = vectorstore.as_retriever(
        search_type='mmr',
        search_kwargs={"k": 4, "fetch_k": 8}
    )

    return MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm
    )

# -------------------------------
# Filters
# -------------------------------
def filter_relevant_docs(docs, query):
    keywords = query.lower().split()
    filtered = []

    for doc in docs:
        text = doc.page_content.lower()
        match_count = sum(1 for word in keywords if word in text)

        if match_count >= 2:
            filtered.append(doc)

    return filtered if filtered else docs


def prioritize_definition(docs):
    keywords = ["what is", "defined as", "is a", "definition"]

    priority = []
    others = []

    for doc in docs:
        text = doc.page_content.lower()

        if any(k in text for k in keywords):
            priority.append(doc)
        else:
            others.append(doc)

    return priority + others


def remove_noise(docs):
    cleaned = []

    for doc in docs:
        text = doc.page_content.strip()

        if len(text) < 50:
            continue
        if text.replace(" ", "").isdigit():
            continue

        cleaned.append(doc)

    return cleaned

# -------------------------------
# Final Answer Function
# -------------------------------
def get_answer(retriever, query):
    docs = retriever.invoke(query)

    docs = remove_noise(docs)
    docs = filter_relevant_docs(docs, query)
    docs = prioritize_definition(docs)

    docs = docs[:3]

    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""
    Answer clearly using the context.

    Context:
    {context}

    Question:
    {query}
    """

    response = llm.invoke(prompt)

    return response.content