from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    # MongoDB
    mongo_url: str = Field(default="mongodb://localhost:27017", env="MONGO_URL")
    mongo_db_name: str = Field(default="messaging_app", env="MONGO_DB_NAME")
    
    # JWT
    jwt_secret: str = Field(default="your-secret-key-change-this", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Encryption
    app_encryption_key: str = Field(..., env="APP_ENCRYPTION_KEY")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

