"""
Centralized Configuration Module
Loads environment variables from .env file
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Load .env file at module import time
from dotenv import load_dotenv

# Find .env file in project root
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables from .env file
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # Try to load from current working directory
    load_dotenv()


@dataclass
class Settings:
    """
    Application settings loaded from environment variables
    
    All sensitive values are kept secure and never exposed in logs/responses
    """
    
    # Groq API Configuration
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    GROQ_TEMPERATURE: float = 0.1
    GROQ_MAX_TOKENS: int = 1024
    
    # Pinecone Configuration (for future use)
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: str = "mutual-funds"
    PINECONE_ENVIRONMENT: str = "us-east-1"
    
    # Application Configuration
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    def __post_init__(self):
        """Load values from environment variables"""
        # Groq settings
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", self.GROQ_MODEL)
        self.GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", self.GROQ_TEMPERATURE))
        self.GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", self.GROQ_MAX_TOKENS))
        
        # Pinecone settings
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        self.PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", self.PINECONE_INDEX_NAME)
        self.PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", self.PINECONE_ENVIRONMENT)
        
        # App settings
        self.DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", self.LOG_LEVEL)
    
    @property
    def groq_configured(self) -> bool:
        """Check if Groq API key is configured"""
        return self.GROQ_API_KEY is not None and self.GROQ_API_KEY != "your_groq_api_key_here"
    
    @property
    def pinecone_configured(self) -> bool:
        """Check if Pinecone API key is configured"""
        return self.PINECONE_API_KEY is not None and self.PINECONE_API_KEY != "your_pinecone_api_key_here"
    
    def validate_groq(self) -> None:
        """Validate Groq configuration, raise error if not configured"""
        if not self.groq_configured:
            raise ValueError(
                "GROQ_API_KEY not configured. "
                "Please set it in the .env file or environment variables. "
                "Get your API key from: https://console.groq.com/keys"
            )
    
    def get_safe_settings(self) -> dict:
        """
        Get settings dictionary with sensitive values masked
        Use this for logging or API responses - NEVER expose API keys
        """
        return {
            "GROQ_MODEL": self.GROQ_MODEL,
            "GROQ_TEMPERATURE": self.GROQ_TEMPERATURE,
            "GROQ_MAX_TOKENS": self.GROQ_MAX_TOKENS,
            "GROQ_API_KEY": "***MASKED***" if self.GROQ_API_KEY else None,
            "GROQ_CONFIGURED": self.groq_configured,
            "PINECONE_INDEX_NAME": self.PINECONE_INDEX_NAME,
            "PINECONE_ENVIRONMENT": self.PINECONE_ENVIRONMENT,
            "PINECONE_API_KEY": "***MASKED***" if self.PINECONE_API_KEY else None,
            "PINECONE_CONFIGURED": self.pinecone_configured,
            "DEBUG": self.DEBUG,
            "LOG_LEVEL": self.LOG_LEVEL,
        }


# Global settings instance (singleton pattern)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create settings singleton
    
    Returns:
        Settings instance with loaded environment variables
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables
    Useful for testing or when .env file changes
    
    Returns:
        Fresh Settings instance
    """
    global _settings
    # Reload .env file
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=True)
    _settings = Settings()
    return _settings


# Convenience function for getting Groq API key
def get_groq_api_key() -> str:
    """
    Get Groq API key from settings
    
    Raises:
        ValueError: If GROQ_API_KEY is not configured
    """
    settings = get_settings()
    settings.validate_groq()
    return settings.GROQ_API_KEY


if __name__ == "__main__":
    # Test configuration loading
    print("Testing Configuration Loading")
    print("=" * 70)
    
    settings = get_settings()
    
    print("\nSafe Settings (for logging):")
    safe = settings.get_safe_settings()
    for key, value in safe.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print(f"Groq Configured: {settings.groq_configured}")
    print(f"Pinecone Configured: {settings.pinecone_configured}")
    
    # Test validation
    print("\nTesting validation:")
    try:
        settings.validate_groq()
        print("  ✓ Groq configuration valid")
    except ValueError as e:
        print(f"  ✗ {e}")
