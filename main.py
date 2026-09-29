import os
import sys
import customtkinter as ctk

# Ensure root directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.gui.theme import Theme
from src.crypto_engine import CryptoEngine
from src.database import Database
from src.gui.auth_window import AuthWindow
from src.gui.main_window import MainWindow

class CyberVaultApp(ctk.CTk):
    """
    Main CyberVault Application Window Controller.
    Manages view transitions between Authentication and Main Vault Console.
    """
    def __init__(self):
        super().__init__()

        # Apply Sci-Fi Cyberpunk Theme
        Theme.apply_theme()

        self.title("CYBERVAULT // Sci-Fi Password Manager & Cryptographic Generator")
        self.geometry("1080x720")
        self.minsize(820, 540)
        self.resizable(True, True)
        self.configure(fg_color=Theme.BG_DARK)

        self.crypto = CryptoEngine()
        self.db = None
        self.current_frame = None

        self.show_auth_screen()

    def show_auth_screen(self):
        """Displays the Master Password unlock/setup screen."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = AuthWindow(
            self,
            crypto=self.crypto,
            on_authenticated=self.on_authenticated
        )

    def on_authenticated(self):
        """Callback when user enters correct master password."""
        # Initialize database with decrypted cipher engine
        self.db = Database(self.crypto)

        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = MainWindow(
            self,
            crypto=self.crypto,
            db=self.db,
            on_lock=self.show_auth_screen
        )

if __name__ == "__main__":
    app = CyberVaultApp()
    app.mainloop()
