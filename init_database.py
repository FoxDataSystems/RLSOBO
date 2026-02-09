"""
Script om de SQLite database te initialiseren met testdata
"""
import sqlite3
from pathlib import Path
from app.config import settings
from app.database import DatabaseConnection


def init_database():
    """Initialiseer de database met schema en testdata"""
    print("Initialiseren van SQLite database...")
    
    # Maak database connection
    db = DatabaseConnection()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Lees SQL script
        sql_file = Path(__file__).parent / "dataset_identity_propagation_sqlite.sql"
        
        if not sql_file.exists():
            print(f"Fout: {sql_file} niet gevonden!")
            return
        
        print(f"Lezen van SQL script: {sql_file}")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Voer SQL script uit
        print("Uitvoeren van SQL script...")
        cursor.executescript(sql_script)
        
        conn.commit()
        print("✓ Database succesvol geïnitialiseerd!")
        print(f"✓ Database locatie: {db.db_path}")
        
        # Toon overzicht
        cursor.execute("SELECT COUNT(*) FROM Gebruikers")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Cliënten")
        client_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Afdelingen")
        dept_count = cursor.fetchone()[0]
        
        print(f"\nDatabase overzicht:")
        print(f"  - Gebruikers: {user_count}")
        print(f"  - Cliënten: {client_count}")
        print(f"  - Afdelingen: {dept_count}")
        
    except Exception as e:
        print(f"Fout bij initialiseren database: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    init_database()

