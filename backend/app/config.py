from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import sys


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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is strong and not the default value"""
        default_secrets = [
            "your-secret-key-change-this",
            "secret",
            "changeme",
            "default",
            "test"
        ]
        
        if v.lower() in default_secrets:
            print("ERROR: JWT_SECRET must be changed from default value!", file=sys.stderr)
            print("Please set a strong, random JWT_SECRET in your .env file", file=sys.stderr)
            sys.exit(1)
        
        if len(v) < 32:
            print("ERROR: JWT_SECRET must be at least 32 characters long!", file=sys.stderr)
            sys.exit(1)
        
        return v


settings = Settings()

