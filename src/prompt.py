# src/prompt.py

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

from langchain_ollama import ChatOllama


# ---------------------------
# Session Store (Memory)
# ---------------------------
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# ---------------------------
# Prompt Template
# ---------------------------
def get_prompt_template():
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful medical assistant. "
                "Use the following retrieved context to answer the question clearly.\n\n"
                "{context}"
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ]
    )


# ---------------------------
# Load LLM
# ---------------------------
def load_llm():
    return ChatOllama(
        model="llama3",
        temperature=0
    )


# ---------------------------
# Build RAG Chain With Memory
# ---------------------------
def build_rag_chain(retriever):

    prompt = get_prompt_template()
    llm = load_llm()

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # 🔥 Extract user input properly
    rag_chain = (
        {
            "context": lambda x: format_docs(retriever.invoke(x["input"])),
            "input": lambda x: x["input"],
            "history": lambda x: x["history"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    rag_chain_with_memory = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    return rag_chain_with_memory