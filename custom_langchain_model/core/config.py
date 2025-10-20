from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    API_OAUTH_URL: str
    API_BASE_URL : str
    API_KEY: str 
    API_SECRET: str

    model_config = ConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="allow"
    )


def get_settings() -> Settings:
    return Settings()


settings = get_settings()