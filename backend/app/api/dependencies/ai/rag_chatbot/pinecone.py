# app/api/dependencies/ai/rag_chatbot/pinecone.py
"""
RAG ingestion pipeline.

Run this once (or whenever your PDF corpus changes) to populate the Pinecone
index.  It no longer depends on torch / sentence-transformers; embeddings are
produced by the Ollama instance configured in your .env file.
"""
import logging
import os
from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pinecone index dimension for nomic-embed-text is 768.
# If you switch embedding models update this constant accordingly.
EMBEDDING_DIMENSION = 768


class RAGPipeline:
    def __init__(
        self,
        source_dir: str = "/content/pdf",
        index_name: str = "rag-chatbot",
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ):
        self.source_dir = Path(source_dir)
        self.index_name = index_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.embedding: OllamaEmbeddings | None = None
        self.pc: Pinecone | None = None
        self.index = None
        self.docsearch: PineconeVectorStore | None = None

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _make_embeddings(self) -> OllamaEmbeddings:
        kwargs: dict = dict(
            model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        )
        api_key = os.getenv("OLLAMA_API_KEY", "")
        base_url = os.getenv("OLLAMA_BASE_URL", "")
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        return OllamaEmbeddings(**kwargs)

    def setup_embeddings(self):
        """Initialise Ollama embeddings."""
        try:
            self.embedding = self._make_embeddings()
            model_name = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
            logger.info(f"Embeddings initialised with Ollama model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialise embeddings: {e}")
            raise

    def setup_pinecone(self):
        """Initialise Pinecone connection and index."""
        try:
            pinecone_api_key = os.getenv("PINECONE_API_KEY")
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY environment variable not set")

            self.pc = Pinecone(api_key=pinecone_api_key)

            if not self.pc.has_index(self.index_name):
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=EMBEDDING_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
            else:
                logger.info(f"Using existing Pinecone index: {self.index_name}")

            self.index = self.pc.Index(self.index_name)

        except Exception as e:
            logger.error(f"Failed to setup Pinecone: {e}")
            raise

    # ------------------------------------------------------------------
    # Document processing
    # ------------------------------------------------------------------

    def load_pdfs(self) -> List[Document]:
        docs: List[Document] = []
        if not self.source_dir.exists():
            logger.warning(f"Source directory {self.source_dir} does not exist")
            return docs

        pdf_files = list(self.source_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")

        for pdf_file in pdf_files:
            try:
                logger.info(f"Loading PDF: {pdf_file.name}")
                docs.extend(PyPDFLoader(str(pdf_file)).load())
            except Exception as e:
                logger.error(f"Failed to load PDF {pdf_file.name}: {e}")

        logger.info(f"Loaded {len(docs)} document pages")
        return docs

    def filter_documents(self, docs: List[Document]) -> List[Document]:
        return [
            Document(
                page_content=doc.page_content,
                metadata={"source": doc.metadata.get("source", "unknown")},
            )
            for doc in docs
        ]

    def split_documents(self, docs: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )
        chunks = splitter.split_documents(docs)
        logger.info(f"Split documents into {len(chunks)} chunks")
        return chunks

    # ------------------------------------------------------------------
    # Vector store helpers
    # ------------------------------------------------------------------

    def create_vector_store(self, chunks: List[Document]) -> PineconeVectorStore:
        try:
            logger.info("Creating vector store from documents...")
            docsearch = PineconeVectorStore.from_documents(
                documents=chunks, embedding=self.embedding, index_name=self.index_name
            )
            logger.info("Vector store created successfully")
            return docsearch
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise

    def load_existing_vector_store(self) -> PineconeVectorStore:
        try:
            logger.info("Loading existing vector store...")
            docsearch = PineconeVectorStore.from_existing_index(
                index_name=self.index_name, embedding=self.embedding
            )
            logger.info("Existing vector store loaded successfully")
            return docsearch
        except Exception as e:
            logger.error(f"Failed to load existing vector store: {e}")
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def setup_full_pipeline(self, force_recreate: bool = False):
        """Setup the complete RAG pipeline."""
        self.setup_embeddings()
        self.setup_pinecone()

        if force_recreate or not self.pc.has_index(self.index_name):
            docs = self.load_pdfs()
            if not docs:
                logger.warning("No documents loaded. Vector store will be empty.")
                return
            filtered = self.filter_documents(docs)
            chunks = self.split_documents(filtered)
            self.docsearch = self.create_vector_store(chunks)
        else:
            self.docsearch = self.load_existing_vector_store()

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        if not self.docsearch:
            raise ValueError(
                "Vector store not initialised. Run setup_full_pipeline() first."
            )
        try:
            results = self.docsearch.similarity_search(query, k=k)
            logger.info(f"Found {len(results)} similar documents")
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise


# ------------------------------------------------------------------
# CLI entry-point
# ------------------------------------------------------------------

def main():
    rag = RAGPipeline(
        source_dir="/content/pdf",
        index_name="rag-chatbot",
        chunk_size=800,
        chunk_overlap=100,
    )
    rag.setup_full_pipeline()

    query = "What is the main topic discussed in the documents?"
    results = rag.similarity_search(query, k=3)
    for i, doc in enumerate(results):
        print(f"Result {i + 1}:")
        print(f"Source: {doc.metadata['source']}")
        print(f"Content: {doc.page_content[:200]}...")
        print("-" * 50)


if __name__ == "__main__":
    main()