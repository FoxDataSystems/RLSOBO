"""
Configuratie instellingen
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Applicatie instellingen"""
    
    # Database instellingen (SQLite)
    DATABASE_NAME: str = "IdentityPropagationDB"
    
    # Azure AD instellingen (optioneel voor productie)
    AZURE_AD_TENANT_ID: Optional[str] = None
    AZURE_AD_CLIENT_ID: Optional[str] = None
    AZURE_AD_CLIENT_SECRET: Optional[str] = None
    AZURE_AD_AUTHORITY: Optional[str] = None
    
    # Applicatie instellingen
    SECRET_KEY: str = "development-secret-key-change-in-production"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

