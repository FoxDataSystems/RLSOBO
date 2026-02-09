"""
Database connectie en configuratie voor SQLite
"""
import sqlite3
import os
from typing import Optional
from pathlib import Path
from app.config import settings


class DatabaseConnection:
    """Database connection manager voor SQLite"""
    
    def __init__(self):
        self.db_path = self._get_db_path()
        self._ensure_database_exists()
    
    def _get_db_path(self) -> Path:
        """Haal database pad op"""
        db_name = settings.DATABASE_NAME
        if not db_name.endswith('.db'):
            db_name += '.db'
        
        # Maak data directory aan als die niet bestaat
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        return data_dir / db_name
    
    def _ensure_database_exists(self):
        """Zorg dat database bestaat"""
        if not self.db_path.exists():
            # Database wordt automatisch aangemaakt bij eerste connectie
            conn = sqlite3.connect(str(self.db_path))
            conn.close()
    
    def get_connection(self):
        """Haal een database connectie op"""
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False  # Voor FastAPI
            )
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            raise Exception(f"Database connectie fout: {str(e)}")


# Global database instance
_db: Optional[DatabaseConnection] = None
_current_user_id: Optional[int] = None


def get_database() -> DatabaseConnection:
    """Haal database instance op"""
    global _db
    if _db is None:
        _db = DatabaseConnection()
    return _db


async def get_db_connection():
    """Async database connection getter"""
    db = get_database()
    return db.get_connection()


def set_current_user_id(user_id: Optional[int]):
    """
    Stel huidige gebruiker ID in voor applicatie-level RLS
    SQLite heeft geen RLS, dus we doen dit op applicatie niveau
    """
    global _current_user_id
    _current_user_id = user_id


def get_current_user_id() -> Optional[int]:
    """Haal huidige gebruiker ID op"""
    return _current_user_id

