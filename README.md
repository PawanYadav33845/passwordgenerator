# ⚡ CYBERVAULT v2.0
> **Sci-Fi Cyberpunk Password Generator & Encrypted Vault Manager**

CYBERVAULT is an all-in-one desktop security application built in Python using CustomTkinter. It features a futuristic Cyberpunk HUD interface, cryptographically secure password generation (CSPRNG), and authenticated AES-256 (Fernet) field-level encryption combined with PBKDF2-HMAC-SHA256 key derivation for all stored database records.

---

## 🔒 Zero-Knowledge Security & Master Password Protection

### Zero-Knowledge Architecture
- **Zero Plaintext Secret Storage**: Master passwords are **never stored anywhere** on disk, in source code, in config files, or in comments.
- **Adaptive One-Way Hashing**: Verification uses salted `bcrypt` hashes. It is mathematically impossible to reverse-engineer or extract the master password from application files or commands.
- **Dynamic RAM-Only Key Derivation**: The 256-bit AES encryption key is derived dynamically in memory at runtime via **PBKDF2-HMAC-SHA256** (200,000 iterations) using your entered Master Password + salt. Upon locking the vault or closing the application, all key material is immediately purged from RAM.

---

## 🌐 Multi-Device Access & Vault Synchronization

CYBERVAULT supports two secure methods for multi-device cross-platform synchronization:

### Method A: Cloud Drive / Shared Folder Auto-Sync (Recommended)
1. Store or copy the `data/` folder (`config.json` and `vault.db`) to your preferred cloud drive directory (e.g., OneDrive, Google Drive, Dropbox, iCloud, or a USB flash drive).
2. Install CYBERVAULT on your second PC or laptop and copy/link the `data/` folder there.
3. Launch `python passwrdmngr.py` on any device and enter your Master Password. All database updates sync seamlessly across devices.

### Method B: Portable `.cybervault` Encrypted Bundle Export
1. In CYBERVAULT, navigate to the **BACKUP & SETTINGS** tab.
2. Click **EXPORT PORTABLE VAULT (.cybervault)**.
3. Move the `.cybervault` bundle file to your second device via email, USB stick, or secure transfer.
4. On the second device, launch CYBERVAULT and click **IMPORT PORTABLE VAULT (.cybervault)** to import all encrypted records!

---

## 🛡️ Database Encryption Specification

1. **Master Key Derivation (PBKDF2-HMAC-SHA256)**:
   - Uses a unique 16-byte random salt stored per-vault.
   - Derives a 256-bit encryption key from your Master Password using 200,000 PBKDF2 hashing iterations.

2. **Database Field Encryption**:
   - SQLite Database (`data/vault.db`) stores **zero plaintext user data**.
   - All columns (`website`, `username`, `password`, `category`, `notes`) are encrypted with AES-256 (Fernet cipher tokens) prior to insertion into the database.
   - Includes an encrypted verification **canary token** in `data/config.json` to validate master key integrity upon login.

3. **Cryptographic Password Generation (CSPRNG)**:
   - Uses Python's `secrets` library to ensure true cryptographic entropy for generated passwords.
   - Computes real-time password entropy in bits ($E = L \times \log_2(N)$).

4. **Memory & Clipboard Sanitization**:
   - Automatic **30-second Clipboard Auto-Clear Timer** to wipe copied passwords from system memory.

---

## 🎨 Sci-Fi GUI Features

- **Cyberpunk HUD Aesthetics**: High-contrast dark void background (`#090C15`) with Cyber Cyan (`#00F0FF`), Holo Green (`#00FF66`), and Plasma Red (`#FF2A6D`) UI accents.
- **Real-Time Telemetry Bar**: Shows active cipher parameters (`AES-256-Fernet | PBKDF2-SHA256`), clipboard countdown status, and one-click vault locking.
- **Password Strength & Entropy Visualizer**: Displays live bit-entropy calculations (`WEAK`, `MEDIUM`, `STRONG`, `OVERKILL`).
- **Security Audit Dashboard**: Automatically scans vault entries for weak passwords (< 50 bits entropy) and password reuse across services.

---

## 📁 Project Architecture

```
password generator/
├── data/                       # Application data & encrypted database
│   ├── config.json             # Salt, bcrypt master hash & encrypted canary token
│   └── vault.db                # Encrypted SQLite credential database
├── src/                        # Source modules
│   ├── __init__.py
│   ├── crypto_engine.py        # PBKDF2 key derivation & Fernet cipher engine
│   ├── generator.py            # CSPRNG password generator & entropy calculator
│   ├── database.py             # Encrypted SQLite database layer
│   ├── backup_manager.py       # Encrypted JSON & CSV import/export manager
│   └── gui/                    # CustomTkinter GUI components
│       ├── __init__.py
│       ├── theme.py            # Sci-Fi color palette & typography
│       ├── auth_window.py      # Master Password authentication window
│       └── main_window.py      # Main Vault, Generator & Audit interface
├── passwrdmngr.py              # Primary Application Entry Point
├── requirements.txt            # Project dependencies
└── README.md                   # System documentation & security report
```

---

## 🚀 How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Application**:
   ```bash
   python passwrdmngr.py
   ```
