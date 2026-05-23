# app/config/settings.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Life Skills World"
    debug: bool = False
    environment: str = "development"

    # Firebase Configuration
    firebase_project_id: str
    firebase_private_key_id: str
    firebase_private_key: str
    firebase_client_email: str
    firebase_client_id: str
    firebase_auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    firebase_token_uri: str = "https://oauth2.googleapis.com/token"

    # Ollama Configuration
    # cloud.ollama.com: set OLLAMA_API_KEY and OLLAMA_MODEL — no base URL needed.
    # Local Ollama: set OLLAMA_BASE_URL (default http://localhost:11434) and
    # leave OLLAMA_API_KEY empty.
    ollama_base_url: str = ""          # leave blank for cloud.ollama.com
    ollama_model: str = "gemma3:4b"
    ollama_api_key: str = ""           # required for cloud.ollama.com
    # Embedding model served by the same Ollama instance
    ollama_embedding_model: str = "nomic-embed-text"

    # LangSmith Configuration
    langsmith_tracing: bool = False
    langsmith_api_key: str
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_project: str

    # Vector store
    pinecone_api_key: str

    # Search
    tavily_api_key: str

    # Voice
    vapi_api_key: str
    vapi_public_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()