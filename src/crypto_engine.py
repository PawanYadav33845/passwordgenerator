import os
import json
import base64
import bcrypt
from typing import Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

class CryptoEngine:
    """
    Handles cryptographic key derivation, master password verification, 
    and authenticated AES encryption/decryption for credentials.
    """
    ITERATIONS = 200_000

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.cipher: Optional[Fernet] = None
        self._salt: Optional[bytes] = None

    def is_initialized(self) -> bool:
        """Returns True if a master password has already been set up."""
        if not os.path.exists(CONFIG_FILE):
            return False
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return "master_hash" in data and "salt" in data
        except Exception:
            return False

    def setup_master_password(self, master_password: str) -> bool:
        """Sets up a new master password and initializes the salt and encryption cipher."""
        if not master_password or len(master_password) < 6:
            raise ValueError("Master password must be at least 6 characters long.")

        salt = os.urandom(16)
        hashed_master = bcrypt.hashpw(master_password.encode('utf-8'), bcrypt.gensalt(12))

        config_data = {
            "master_hash": hashed_master.decode('utf-8'),
            "salt": base64.b64encode(salt).decode('utf-8'),
            "iterations": self.ITERATIONS
        }

        self._salt = salt
        self.cipher = self._derive_cipher(master_password, salt)

        # Store encrypted canary token to verify encryption key integrity
        canary = self.encrypt("CYBERVAULT_CANARY_OK")

        config_data = {
            "master_hash": hashed_master.decode('utf-8'),
            "salt": base64.b64encode(salt).decode('utf-8'),
            "iterations": self.ITERATIONS,
            "canary": canary
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)

        return True

    def verify_and_login(self, master_password: str) -> bool:
        """Verifies master password and initializes Fernet cipher."""
        if not self.is_initialized():
            return False

        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)

        stored_hash = data["master_hash"].encode('utf-8')
        salt = base64.b64decode(data["salt"])

        if bcrypt.checkpw(master_password.encode('utf-8'), stored_hash):
            self._salt = salt
            self.cipher = self._derive_cipher(master_password, salt)
            
            # Check canary token if present
            if "canary" in data:
                try:
                    decrypted_canary = self.decrypt(data["canary"])
                    if decrypted_canary != "CYBERVAULT_CANARY_OK":
                        self.lock_vault()
                        return False
                except Exception:
                    self.lock_vault()
                    return False
            return True
        return False

    def lock_vault(self):
        """Clears memory references to encryption key."""
        self.cipher = None
        self._salt = None

    def _derive_cipher(self, master_password: str, salt: bytes) -> Fernet:
        """Derives a Fernet key from master password using PBKDF2HMAC-SHA256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.ITERATIONS
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode('utf-8')))
        return Fernet(key)

    def encrypt(self, text: str) -> str:
        """Encrypts a plaintext string into a base64 encoded ciphertext token."""
        if not self.cipher:
            raise RuntimeError("Vault is locked. Authenticate first.")
        if not text:
            return ""
        encrypted_bytes = self.cipher.encrypt(text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def decrypt(self, token: str) -> str:
        """Decrypts an encrypted token back into plaintext string."""
        if not self.cipher:
            raise RuntimeError("Vault is locked. Authenticate first.")
        if not token:
            return ""
        decrypted_bytes = self.cipher.decrypt(token.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
