import json
import csv
import os
import base64
from typing import List, Dict, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.database import Database
from src.crypto_engine import CryptoEngine

class BackupManager:
    """
    Handles secure encrypted backup exports/imports and CSV import/export for CyberVault.
    """
    @staticmethod
    def export_encrypted_backup(file_path: str, backup_password: str, db: Database) -> bool:
        """Exports vault credentials to an encrypted JSON backup file using backup_password."""
        if not backup_password or len(backup_password) < 6:
            raise ValueError("Backup password must be at least 6 characters long.")

        credentials = db.get_all_credentials()
        salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=150_000
        )
        key = base64.urlsafe_b64encode(kdf.derive(backup_password.encode('utf-8')))
        cipher = Fernet(key)

        raw_json = json.dumps(credentials).encode('utf-8')
        encrypted_payload = cipher.encrypt(raw_json).decode('utf-8')

        backup_data = {
            "version": "2.0.0",
            "salt": base64.b64encode(salt).decode('utf-8'),
            "payload": encrypted_payload
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=4)
        return True

    @staticmethod
    def export_portable_vault(file_path: str, master_password: str, db: Database) -> bool:
        """Exports full encrypted portable vault bundle (.cybervault) for cross-device sync."""
        return BackupManager.export_encrypted_backup(file_path, master_password, db)

    @staticmethod
    def import_portable_vault(file_path: str, master_password: str, db: Database) -> int:
        """Imports encrypted portable vault bundle (.cybervault) into current vault."""
        return BackupManager.import_encrypted_backup(file_path, master_password, db)

    @staticmethod
    def import_encrypted_backup(file_path: str, backup_password: str, db: Database) -> int:
        """Imports credentials from an encrypted JSON backup file using backup_password."""
        with open(file_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        if "salt" not in backup_data or "payload" not in backup_data:
            raise ValueError("Invalid backup file format.")

        salt = base64.b64decode(backup_data["salt"])
        payload = backup_data["payload"].encode('utf-8')

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=150_000
        )
        key = base64.urlsafe_b64encode(kdf.derive(backup_password.encode('utf-8')))
        cipher = Fernet(key)

        decrypted_bytes = cipher.decrypt(payload)
        credentials = json.loads(decrypted_bytes.decode('utf-8'))

        imported_count = 0
        for item in credentials:
            if isinstance(item, dict) and "website" in item and "username" in item and "password" in item:
                db.add_credential(
                    website=item["website"],
                    username=item["username"],
                    password=item["password"],
                    category=item.get("category", "Imported"),
                    notes=item.get("notes", "")
                )
                imported_count += 1

        return imported_count

    @staticmethod
    def export_csv(file_path: str, db: Database) -> int:
        """Exports credentials to plain CSV file."""
        credentials = db.get_all_credentials()
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Website", "Username", "Password", "Category", "Notes"])
            for item in credentials:
                writer.writerow([
                    item["website"],
                    item["username"],
                    item["password"],
                    item["category"],
                    item["notes"]
                ])
        return len(credentials)

    @staticmethod
    def import_csv(file_path: str, db: Database) -> int:
        """Imports credentials from a CSV file."""
        imported_count = 0
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            for row in reader:
                if not row or len(row) < 3:
                    continue
                website = row[0].strip()
                username = row[1].strip()
                password = row[2].strip()
                category = row[3].strip() if len(row) > 3 else "General"
                notes = row[4].strip() if len(row) > 4 else ""

                if website and username and password:
                    db.add_credential(website, username, password, category, notes)
                    imported_count += 1
        return imported_count
