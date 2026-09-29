import os
import sqlite3
from typing import List, Dict, Optional, Tuple
from src.crypto_engine import CryptoEngine

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_FILE = os.path.join(DATA_DIR, "vault.db")

class Database:
    """
    SQLite Database Manager for CyberVault.
    All sensitive fields (website, username, password, category, notes) are stored encrypted.
    """
    def __init__(self, crypto: CryptoEngine):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.crypto = crypto
        self.db_path = DB_FILE
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                category TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()

    def add_credential(self, website: str, username: str, password: str, category: str = "General", notes: str = "") -> int:
        """Encrypts and inserts a new credential entry into the database."""
        enc_website = self.crypto.encrypt(website)
        enc_username = self.crypto.encrypt(username)
        enc_password = self.crypto.encrypt(password)
        enc_category = self.crypto.encrypt(category)
        enc_notes = self.crypto.encrypt(notes) if notes else ""

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO credentials (website, username, password, category, notes)
            VALUES (?, ?, ?, ?, ?)
            """, (enc_website, enc_username, enc_password, enc_category, enc_notes))
            conn.commit()
            return cursor.lastrowid

    def update_credential(self, entry_id: int, website: str, username: str, password: str, category: str = "General", notes: str = "") -> bool:
        """Encrypts and updates an existing credential entry."""
        enc_website = self.crypto.encrypt(website)
        enc_username = self.crypto.encrypt(username)
        enc_password = self.crypto.encrypt(password)
        enc_category = self.crypto.encrypt(category)
        enc_notes = self.crypto.encrypt(notes) if notes else ""

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE credentials 
            SET website = ?, username = ?, password = ?, category = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (enc_website, enc_username, enc_password, enc_category, enc_notes, entry_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_credential(self, entry_id: int) -> bool:
        """Deletes a credential entry by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM credentials WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_credentials(self) -> List[Dict]:
        """Retrieves and decrypts all credential entries."""
        records = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, website, username, password, category, notes, created_at, updated_at FROM credentials ORDER BY id DESC")
            rows = cursor.fetchall()

        for row in rows:
            entry_id, enc_web, enc_user, enc_pass, enc_cat, enc_notes, created, updated = row
            try:
                website = self.crypto.decrypt(enc_web)
                username = self.crypto.decrypt(enc_user)
                password = self.crypto.decrypt(enc_pass)
                category = self.crypto.decrypt(enc_cat) if enc_cat else "General"
                notes = self.crypto.decrypt(enc_notes) if enc_notes else ""

                records.append({
                    "id": entry_id,
                    "website": website,
                    "username": username,
                    "password": password,
                    "category": category,
                    "notes": notes,
                    "created_at": created,
                    "updated_at": updated
                })
            except Exception as e:
                # Log or handle corrupted/invalid entries safely without crashing
                records.append({
                    "id": entry_id,
                    "website": "[DECRYPTION_ERROR]",
                    "username": "[DECRYPTION_ERROR]",
                    "password": "",
                    "category": "Error",
                    "notes": str(e),
                    "created_at": created,
                    "updated_at": updated
                })
        return records

    def search_credentials(self, query: str) -> List[Dict]:
        """Searches credentials matching the query in website, username, or category."""
        all_records = self.get_all_credentials()
        if not query:
            return all_records
        
        q = query.lower()
        return [
            r for r in all_records
            if q in r["website"].lower() or q in r["username"].lower() or q in r["category"].lower()
        ]
