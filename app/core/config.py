from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "universal-music-api-for-seamusic"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A universal music API for Seamusic - Powered by QQ Music"
    ALLOWED_HOSTS: List[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
