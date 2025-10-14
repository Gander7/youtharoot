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
    
    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-please-make-it-long-and-random")
    
    # Admin User Configuration (for development/initial setup)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: Optional[str] = os.getenv("ADMIN_PASSWORD")  # If not set, random password will be generated
    
    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")
    SMS_MAX_MESSAGES_PER_HOUR: int = int(os.getenv("SMS_MAX_MESSAGES_PER_HOUR", "150"))
    SMS_COST_PER_MESSAGE: float = float(os.getenv("SMS_COST_PER_MESSAGE", "0.0083"))
    
    @property
    def database_url(self) -> Optional[str]:
        """Get the appropriate database URL based on environment"""
        # Only use database if explicitly set to postgresql mode
        if self.DATABASE_TYPE == "postgresql":
            if self.DATABASE_URL:
                return self.DATABASE_URL
            else:
                return self.DEV_DATABASE_URL
        else:
            # Default to memory mode
            return None

settings = Settings()