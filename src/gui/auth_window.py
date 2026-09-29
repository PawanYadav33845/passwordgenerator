import customtkinter as ctk
from tkinter import messagebox
from typing import Callable
from src.gui.theme import Theme
from src.crypto_engine import CryptoEngine

class AuthWindow(ctk.CTkFrame):
    """
    Sci-Fi Authentication Frame for Master Password entry / initial setup.
    """
    def __init__(self, parent, crypto: CryptoEngine, on_authenticated: Callable):
        super().__init__(parent, fg_color=Theme.BG_DARK)
        self.parent = parent
        self.crypto = crypto
        self.on_authenticated = on_authenticated

        self.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self):
        # Outer Card Container
        card = ctk.CTkFrame(
            self,
            fg_color=Theme.PANEL_BG,
            border_color=Theme.CYAN,
            border_width=2,
            corner_radius=12,
            width=420,
            height=480
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # Header Title
        title_label = ctk.CTkLabel(
            card,
            text="CYBERVAULT",
            font=("Segoe UI", 26, "bold"),
            text_color=Theme.CYAN
        )
        title_label.pack(pady=(35, 5))

        subtitle_label = ctk.CTkLabel(
            card,
            text="[ SECURITY GATEWAY v2.0 ]",
            font=Theme.FONT_HUD,
            text_color=Theme.TEXT_SECONDARY
        )
        subtitle_label.pack(pady=(0, 20))

        # Status Tag
        is_init = self.crypto.is_initialized()
        status_text = "AUTHENTICATION REQUIRED" if is_init else "INITIAL SETUP: CREATE MASTER KEY"
        status_color = Theme.AMBER if not is_init else Theme.GREEN

        status_badge = ctk.CTkLabel(
            card,
            text=f"● {status_text}",
            font=Theme.FONT_HUD,
            text_color=status_color
        )
        status_badge.pack(pady=(0, 25))

        # Password Entry Label & Input
        entry_lbl_text = "ENTER MASTER PASSWORD:" if is_init else "CREATE MASTER PASSWORD:"
        ctk.CTkLabel(
            card,
            text=entry_lbl_text,
            font=Theme.FONT_HUD,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", padx=40, pady=(0, 5))

        self.pass_entry = ctk.CTkEntry(
            card,
            placeholder_text="••••••••••••••••",
            show="*",
            font=Theme.FONT_MONO,
            fg_color=Theme.CARD_BG,
            border_color=Theme.PANEL_BORDER,
            text_color=Theme.TEXT_MAIN,
            height=40,
            corner_radius=8
        )
        self.pass_entry.pack(fill="x", padx=40, pady=(0, 15))
        self.pass_entry.focus()
        self.pass_entry.bind("<Return>", lambda e: self._handle_submit())

        # Confirmation Entry if Initial Setup
        self.confirm_entry = None
        if not is_init:
            ctk.CTkLabel(
                card,
                text="CONFIRM MASTER PASSWORD:",
                font=Theme.FONT_HUD,
                text_color=Theme.TEXT_SECONDARY,
                anchor="w"
            ).pack(fill="x", padx=40, pady=(0, 5))

            self.confirm_entry = ctk.CTkEntry(
                card,
                placeholder_text="••••••••••••••••",
                show="*",
                font=Theme.FONT_MONO,
                fg_color=Theme.CARD_BG,
                border_color=Theme.PANEL_BORDER,
                text_color=Theme.TEXT_MAIN,
                height=40,
                corner_radius=8
            )
            self.confirm_entry.pack(fill="x", padx=40, pady=(0, 15))
            self.confirm_entry.bind("<Return>", lambda e: self._handle_submit())

        # Submit Action Button
        btn_text = "UNLOCK VAULT" if is_init else "INITIALIZE VAULT"
        btn_color = Theme.CYAN if is_init else Theme.GREEN

        self.action_btn = ctk.CTkButton(
            card,
            text=btn_text,
            font=Theme.FONT_HEADER,
            fg_color=btn_color,
            text_color="#000000",
            hover_color=Theme.BLUE,
            height=44,
            corner_radius=8,
            command=self._handle_submit
        )
        self.action_btn.pack(fill="x", padx=40, pady=(15, 10))

        # Security Protocol Note
        ctk.CTkLabel(
            card,
            text="AES-256 / PBKDF2-HMAC-SHA256 ENCRYPTED",
            font=("Segoe UI", 9),
            text_color=Theme.TEXT_MUTED
        ).pack(pady=(15, 0))

    def _handle_submit(self):
        password = self.pass_entry.get().strip()

        if not password:
            messagebox.showwarning("Input Error", "Master password field cannot be empty.")
            return

        if not self.crypto.is_initialized():
            confirm = self.confirm_entry.get().strip() if self.confirm_entry else ""
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match!")
                return
            if len(password) < 6:
                messagebox.showerror("Security Warning", "Master password must be at least 6 characters.")
                return
            try:
                self.crypto.setup_master_password(password)
                messagebox.showinfo("Vault Initialized", "Master key established successfully! Vault is now ready.")
                self.on_authenticated()
            except Exception as e:
                messagebox.showerror("Initialization Failed", str(e))
        else:
            if self.crypto.verify_and_login(password):
                self.on_authenticated()
            else:
                messagebox.showerror("Access Denied", "Invalid Master Password. Encryption key refused.")
                self.pass_entry.delete(0, 'end')
