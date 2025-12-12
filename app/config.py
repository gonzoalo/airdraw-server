from pydantic_settings import BaseSettings
import logging

class Settings(BaseSettings):
    app_name: str = "AirDraw Server"
    debug: bool = True
    cors_origins: list = ["http://localhost:5173"]
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()