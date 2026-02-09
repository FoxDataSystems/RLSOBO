"""
Database connectie en configuratie voor SQLite.
Database wordt automatisch geïnitialiseerd met schema en testdata uit app.schema (geen extern bestand nodig).
"""
import sqlite3
from typing import Optional
from pathlib import Path
from app.config import settings
from app.schema import get_schema_sql


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
    
    def _schema_is_initialized(self, conn: sqlite3.Connection) -> bool:
        """Controleer of alle vereiste tabellen bestaan (voorkomt half-geïnitialiseerde DB)."""
        required = {"Gebruikers", "Afdelingen", "Cliënten", "Toegangsrechten"}
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?,?,?)",
            tuple(required),
        )
        found = {row[0] for row in cursor.fetchall()}
        return required.issubset(found)
    
    def _run_schema_script(self, conn: sqlite3.Connection) -> None:
        """Voer schema en testdata uit (uit app.schema, geen extern bestand)."""
        script = get_schema_sql()
        # Alleen uitvoerbare regels; SQLite negeert comments maar executescript kan ze bevatten
        conn.executescript(script)
        conn.commit()
    
    def _ensure_database_exists(self) -> None:
        """Zorg dat database bestaat en zo nodig schema + testdata aanmaken."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            if not self._schema_is_initialized(conn):
                self._run_schema_script(conn)
        finally:
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

