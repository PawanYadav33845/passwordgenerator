# ⚡ CYBERVAULT v2.0
> **Sci-Fi Cyberpunk Password Generator & Encrypted Vault (Desktop + Web Version)**

[![Live Demo](https://img.shields.io/badge/LIVE_DEMO-NETLIFY-00F0FF?style=for-the-badge&logo=netlify)](https://passwordmngen.netlify.app/)

CYBERVAULT is an all-in-one security suite available as both a **Desktop Application (Python/CustomTkinter)** and a **Web Application (HTML5/JavaScript Web-Crypto API)**.

🔗 **Live Web Demo**: [https://passwordmngen.netlify.app/](https://passwordmngen.netlify.app/)

---

## 🌐 Web Version

The Web version of CYBERVAULT runs 100% client-side inside the browser using modern cryptographic standards.

### 🌐 Live Web Demo
👉 **[https://passwordmngen.netlify.app/](https://passwordmngen.netlify.app/)**

### Key Web Features
- **Client-Side Web Crypto API**: Encrypts and decrypts credentials directly in the browser using **AES-256-GCM** with a **PBKDF2-SHA256** derived key (200,000 iterations).
- **CSPRNG Password Generator**: Uses `window.crypto.getRandomValues()` for true cryptographic entropy.
- **Entropy & Strength Meter**: Calculates bit entropy ($E = L \times \log_2(N)$) and assigns live ratings (`WEAK`, `MEDIUM`, `STRONG`, `OVERKILL`).
- **Encrypted Web Vault**: Stores credentials encrypted in `localStorage` or exports to encrypted `.cybervault` bundle files.
- **Clipboard Protection**: 30-second automated clipboard auto-clear timer with visual countdown.

---

## 🖥️ Desktop Version (`main.py`)

### 🔑 Master Password & Security Model
- **Zero-Knowledge Architecture**: Master passwords are never stored on disk or in source code.
- **PBKDF2-HMAC-SHA256 Key Derivation**: 256-bit AES encryption key derived at runtime.
- **Field-Level Encryption**: All SQLite `vault.db` entries (`website`, `username`, `password`, `category`, `notes`) are encrypted with AES-256 (Fernet) prior to database insertion.

### 🚀 How to Run Desktop App

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Launch Desktop Application
python main.py
```

---

## 📁 Project Directory Architecture

```
password-generator/
├── index.html                  # Cyberpunk Web Interface
├── styles.css                  # Sci-Fi Cyberpunk CSS styling & animations
├── app.js                      # Client-Side Web Crypto API controller
├── netlify.toml                # Netlify deployment configuration
├── main.py                     # Desktop Application Entry Point
├── data/                       # Local desktop storage directory
│   ├── config.json             # Salt & bcrypt master hash
│   └── vault.db                # Encrypted SQLite database
├── src/                        # Desktop Python source modules
│   ├── __init__.py
│   ├── crypto_engine.py        # PBKDF2 key derivation & Fernet cipher engine
│   ├── generator.py            # CSPRNG password generator & entropy calculator
│   ├── database.py             # Encrypted SQLite database layer
│   ├── backup_manager.py       # Encrypted JSON & CSV import/export manager
│   └── gui/                    # CustomTkinter GUI components
├── requirements.txt            # Desktop Python dependencies
└── README.md                   # System documentation & live demo link
```
