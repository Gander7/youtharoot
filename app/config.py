import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Database Configuration
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "memory")  # "memory" or "postgresql"
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Development database URL (if using local PostgreSQL)
    DEV_DATABASE_URL: str = os.getenv("DEV_DATABASE_URL", "postgresql://localhost/youth_attendance_dev")
    
    # Application Configuration
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    @property
    def database_url(self) -> Optional[str]:
        """Get the appropriate database URL based on environment"""
        if self.DATABASE_TYPE == "memory":
            return None
        elif self.DATABASE_URL:
            return self.DATABASE_URL
        else:
            return self.DEV_DATABASE_URL

settings = Settings()