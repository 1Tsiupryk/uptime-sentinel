import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.scalar_one() == 1
    except SQLAlchemyError:
        logger.exception("Database connection failed")
        return False