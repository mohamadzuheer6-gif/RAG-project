# src/helpers.py

# src/helpers.py

import os
from typing import List
from dotenv import load_dotenv

# ✅ NEW CORRECT IMPORTS
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitterr
from langchain_core.documents import Document

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore


# -----------------------
# Load Environment
# -----------------------
def load_environment():
    load_dotenv()
    os.environ["PINECONE_API_KEY"] = os.getenv("PINECONE_API_KEY")
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


# -----------------------
# Load PDF Documents
# -----------------------
def load_pdf(data_path: str):
    loader = DirectoryLoader(
        data_path,
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )
    return loader.load()


# -----------------------
# Reduce Metadata
# -----------------------
def filter_to_minimal_docs(docs: List[Document]) -> List[Document]:
    minimal_docs = []
    for doc in docs:
        src = doc.metadata.get("source")
        minimal_docs.append(
            Document(
                page_content=doc.page_content,
                metadata={"source": src}
            )
        )
    return minimal_docs


# -----------------------
# Text Splitting
# -----------------------
def split_documents(docs: List[Document]):
    splitter = RecursiveCharacterTextSplitterr(
        chunk_size=500,
        chunk_overlap=20,
        length_function=len
    )
    return splitter.split_documents(docs)

from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
# -----------------------
# Embeddings
# -----------------------
def download_embeddings():
    model_name = "sentence-transformers/all-MiniLM-L6-v2"

    embeddings = HuggingFaceInferenceAPIEmbeddings(
        api_key=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        model_name=model_name
    )

    return embeddings


# -----------------------
# Pinecone Setup
# -----------------------
def initialize_pinecone(index_name="medibot", dimension=384):
    load_environment()

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    return index_name


# -----------------------
# Create Vector Store
# -----------------------
def create_vector_store(documents, embeddings, index_name):
    return PineconeVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        index_name=index_name
    )


def load_existing_vector_store(embeddings, index_name):
    return PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )


# -----------------------
# Create Retriever
# -----------------------
def create_retriever(vector_store, k=3):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )