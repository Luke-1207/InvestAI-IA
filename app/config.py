import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    ENABLE_PREVIEW_ENDPOINTS: bool = os.getenv("ENABLE_PREVIEW_ENDPOINTS", "true").lower() == "true"


settings = Settings()