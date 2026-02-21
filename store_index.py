# store_index.py

from src.helpers import (
    load_pdf,
    filter_to_minimal_docs,
    split_documents,
    download_embeddings,
    initialize_pinecone,
    create_vector_store,
)

DATA_PATH = "data"          # folder containing PDFs
INDEX_NAME = "medibot"      # same name used in notebook


def main():
    print("🔹 Loading documents...")
    docs = load_pdf(DATA_PATH)

    print(f"✅ Loaded {len(docs)} documents")

    print("🔹 Cleaning metadata...")
    minimal_docs = filter_to_minimal_docs(docs)

    print("🔹 Splitting documents...")
    chunks = split_documents(minimal_docs)

    print(f"✅ Created {len(chunks)} chunks")

    print("🔹 Loading embeddings model...")
    embeddings = download_embeddings()

    print("🔹 Initializing Pinecone index...")
    index_name = initialize_pinecone(INDEX_NAME)

    print("🔹 Storing embeddings in Pinecone...")
    create_vector_store(chunks, embeddings, index_name)

    print("🎉 Indexing completed successfully!")


if __name__ == "__main__":
    main()