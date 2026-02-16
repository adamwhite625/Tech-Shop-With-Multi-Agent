from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "TechStore Host Agent"
    app_version: str = "1.0.0"
    
    # A2A Integration URLs
    search_agent_url: str = "http://localhost:8001"
    advisor_agent_url: str = "http://localhost:8002"
    order_agent_url: str = "http://localhost:8003"
    
    # AI Config
    openai_api_key: str = ""

    # Load from .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global settings instance
settings = Settings()