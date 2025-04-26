import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
os.environ["OPENAI_API_KEY"] = settings.openai_api_key
