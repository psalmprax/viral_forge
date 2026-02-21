from sqlalchemy.orm import Session
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings
from api.config import settings
import logging

logger = logging.getLogger(__name__)

def get_secret(key: str, default=None) -> str:
    """
    Retrieves a secret from the database (SystemSettings).
    If not found, falls back to the environment-based settings.
    """
    db = SessionLocal()
    try:
        # 1. Check Database
        db_setting = db.query(SystemSettings).filter(SystemSettings.key == key.lower()).first()
        if db_setting and db_setting.value:
            return db_setting.value
            
        # 2. Check api.config settings
        # Convert key to uppercase for api.config match (e.g., groq_api_key -> GROQ_API_KEY)
        config_key = key.upper()
        if hasattr(settings, config_key):
            val = getattr(settings, config_key)
            if val:
                return val
                
        return default
    except Exception as e:
        logger.error(f"Error resolving secret {key}: {e}")
        return default
    finally:
        db.close()
