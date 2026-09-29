import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pyperclip
from typing import Callable, Optional, List, Dict

from src.gui.theme import Theme
from src.crypto_engine import CryptoEngine
from src.database import Database
from src.generator import PasswordGenerator
from src.backup_manager import BackupManager

class MainWindow(ctk.CTkFrame):
    """
    Sci-Fi Cyberpunk Integrated Password Manager & Generator Console.
    """
    def __init__(self, parent, crypto: CryptoEngine, db: Database, on_lock: Callable):
        super().__init__(parent, fg_color=Theme.BG_DARK)
        self.parent = parent
        self.crypto = crypto
        self.db = db
        self.on_lock = on_lock

        self._clipboard_timer_id = None
        self._clipboard_seconds_left = 0

        self.pack(fill="both", expand=True)
        self._build_ui()
        self.refresh_vault_list()

    def _build_ui(self):
        # -------------------------------------------------------------
        # 1. TOP HUD BAR
        # -------------------------------------------------------------
        hud_bar = ctk.CTkFrame(
            self,
            fg_color=Theme.PANEL_BG,
            border_color=Theme.PANEL_BORDER,
            border_width=1,
            height=60,
            corner_radius=0
        )
        hud_bar.pack(fill="x", side="top", padx=0, pady=0)
        hud_bar.pack_propagate(False)

        # Title & Subtitle
        title_frame = ctk.CTkFrame(hud_bar, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            title_frame,
            text="CYBERVAULT v2.0",
            font=("Segoe UI", 18, "bold"),
            text_color=Theme.CYAN
        ).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(
            title_frame,
            text="● VAULT UNLOCKED",
            font=Theme.FONT_HUD,
            text_color=Theme.GREEN
        ).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(
            title_frame,
            text="[ CIPHER: AES-256-FERNET | KDF: PBKDF2-SHA256 ]",
            font=Theme.FONT_HUD,
            text_color=Theme.TEXT_MUTED
        ).pack(side="left")

        # Top Right Controls
        controls_frame = ctk.CTkFrame(hud_bar, fg_color="transparent")
        controls_frame.pack(side="right", padx=20, pady=10)

        self.clipboard_status_lbl = ctk.CTkLabel(
            controls_frame,
            text="",
            font=Theme.FONT_HUD,
            text_color=Theme.AMBER
        )
        self.clipboard_status_lbl.pack(side="left", padx=15)

        ctk.CTkButton(
            controls_frame,
            text="🔒 LOCK VAULT",
            font=Theme.FONT_HUD,
            fg_color=Theme.RED,
            hover_color="#CC1144",
            text_color="#FFFFFF",
            width=110,
            height=32,
            corner_radius=6,
            command=self._handle_lock
        ).pack(side="right")

        # -------------------------------------------------------------
        # 2. TABBED MAIN VIEW (Sci-Fi Cyber Tabs)
        # -------------------------------------------------------------
        self.tab_view = ctk.CTkTabview(
            self,
            fg_color=Theme.BG_DARK,
            segmented_button_fg_color=Theme.PANEL_BG,
            segmented_button_selected_color=Theme.CYAN,
            segmented_button_selected_hover_color=Theme.BLUE,
            segmented_button_unselected_color=Theme.PANEL_BG,
            segmented_button_unselected_hover_color=Theme.CARD_BG,
            text_color="#000000"
        )
        self.tab_view.pack(fill="both", expand=True, padx=15, pady=(10, 15))

        self.tab_vault = self.tab_view.add(" 🗄️ CREDENTIALS VAULT ")
        self.tab_generator = self.tab_view.add(" ⚡ PASSWORD GENERATOR ")
        self.tab_audit = self.tab_view.add(" 🛡️ SECURITY AUDIT ")
        self.tab_settings = self.tab_view.add(" ⚙️ BACKUP & SETTINGS ")

        # Build individual tab content
        self._build_vault_tab()
        self._build_generator_tab()
        self._build_audit_tab()
        self._build_settings_tab()

    # =================================================================
    # TAB 1: CREDENTIALS VAULT
    # =================================================================
    def _build_vault_tab(self):
        # Top Action Bar inside Vault Tab (Search & Add New)
        top_bar = ctk.CTkFrame(self.tab_vault, fg_color="transparent")
        top_bar.pack(fill="x", pady=(5, 10))

        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍 Search credentials by website, username or category...",
            font=Theme.FONT_BODY,
            fg_color=Theme.PANEL_BG,
            border_color=Theme.PANEL_BORDER,
            text_color=Theme.TEXT_MAIN,
            height=38,
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_vault_list())

        ctk.CTkButton(
            top_bar,
            text="+ ADD CREDENTIAL",
            font=Theme.FONT_HEADER,
            fg_color=Theme.CYAN,
            text_color="#000000",
            hover_color=Theme.BLUE,
            height=38,
            corner_radius=8,
            command=self._open_add_credential_dialog
        ).pack(side="right")

        # Treeview / Records Container
        list_frame = ctk.CTkFrame(self.tab_vault, fg_color=Theme.PANEL_BG, border_color=Theme.PANEL_BORDER, border_width=1, corner_radius=8)
        list_frame.pack(fill="both", expand=True)

        # Style TTK Treeview to match Sci-Fi dark theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background=Theme.PANEL_BG,
            foreground=Theme.TEXT_MAIN,
            fieldbackground=Theme.PANEL_BG,
            rowheight=32,
            font=Theme.FONT_BODY
        )
        style.configure(
            "Treeview.Heading",
            background=Theme.CARD_BG,
            foreground=Theme.CYAN,
            font=Theme.FONT_HEADER,
            bordercolor=Theme.PANEL_BORDER
        )
        style.map("Treeview", background=[("selected", Theme.BLUE)], foreground=[("selected", "#FFFFFF")])

        cols = ("id", "website", "username", "category", "strength", "updated")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("website", text="WEBSITE / SERVICE")
        self.tree.heading("username", text="ENCRYPTED USERNAME")
        self.tree.heading("category", text="CATEGORY")
        self.tree.heading("strength", text="STRENGTH")
        self.tree.heading("updated", text="LAST UPDATED")

        self.tree.column("id", width=50, minwidth=40, stretch=False, anchor="center")
        self.tree.column("website", width=220, minwidth=140, stretch=True, anchor="w")
        self.tree.column("username", width=200, minwidth=130, stretch=True, anchor="w")
        self.tree.column("category", width=120, minwidth=90, stretch=True, anchor="center")
        self.tree.column("strength", width=120, minwidth=90, stretch=True, anchor="center")
        self.tree.column("updated", width=150, minwidth=110, stretch=True, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        # Action bar at bottom of vault
        bottom_bar = ctk.CTkFrame(self.tab_vault, fg_color="transparent")
        bottom_bar.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            bottom_bar,
            text="📋 COPY USERNAME",
            font=Theme.FONT_HUD,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.BLUE,
            height=32,
            command=self._copy_selected_username
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bottom_bar,
            text="🔑 COPY PASSWORD",
            font=Theme.FONT_HUD,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.CYAN,
            height=32,
            command=self._copy_selected_password
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bottom_bar,
            text="👁️ VIEW / EDIT",
            font=Theme.FONT_HUD,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.AMBER,
            height=32,
            command=self._view_selected_credential
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bottom_bar,
            text="🗑️ DELETE",
            font=Theme.FONT_HUD,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.RED,
            height=32,
            command=self._delete_selected_credential
        ).pack(side="right")

    def refresh_vault_list(self):
        """Reloads and updates the treeview with decrypted data matching search query."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        query = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
        records = self.db.search_credentials(query)

        for rec in records:
            lbl, entropy, color = PasswordGenerator.evaluate_strength(rec["password"])
            strength_str = f"{lbl} ({int(entropy)}b)"
            
            self.tree.insert(
                "",
                "end",
                values=(
                    rec["id"],
                    rec["website"],
                    rec["username"],
                    rec["category"],
                    strength_str,
                    rec["updated_at"]
                )
            )

    # =================================================================
    # TAB 2: PASSWORD GENERATOR
    # =================================================================
    def _build_generator_tab(self):
        panel = ctk.CTkScrollableFrame(self.tab_generator, fg_color=Theme.PANEL_BG, border_color=Theme.PANEL_BORDER, border_width=1, corner_radius=10)
        panel.pack(fill="both", expand=True, padx=20, pady=10)

        # Title
        ctk.CTkLabel(
            panel,
            text="QUANTUM CRYPTOGRAPHIC PASSWORD GENERATOR",
            font=Theme.FONT_TITLE,
            text_color=Theme.CYAN
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            panel,
            text="Generates entropy-driven passwords using Python's CSPRNG (secrets module).",
            font=Theme.FONT_HUD,
            text_color=Theme.TEXT_MUTED
        ).pack(pady=(0, 20))

        # Output Box Frame
        out_frame = ctk.CTkFrame(panel, fg_color=Theme.CARD_BG, border_color=Theme.CYAN, border_width=1, corner_radius=8)
        out_frame.pack(fill="x", padx=40, pady=(0, 15))

        self.gen_password_lbl = ctk.CTkEntry(
            out_frame,
            font=Theme.FONT_MONO_BOLD,
            fg_color="transparent",
            border_width=0,
            text_color=Theme.GREEN,
            justify="center"
        )
        self.gen_password_lbl.pack(fill="x", padx=15, pady=15)

        # Strength Bar
        self.strength_meter = ctk.CTkProgressBar(panel, height=10, corner_radius=5, fg_color=Theme.CARD_BG, progress_color=Theme.CYAN)
        self.strength_meter.pack(fill="x", padx=40, pady=(0, 5))
        self.strength_meter.set(0.8)

        self.strength_desc_lbl = ctk.CTkLabel(
            panel,
            text="STRENGTH: STRONG (85.4 bits entropy)",
            font=Theme.FONT_HUD,
            text_color=Theme.CYAN
        )
        self.strength_desc_lbl.pack(pady=(0, 20))

        # Generator Controls & Sliders
        ctrl_frame = ctk.CTkFrame(panel, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=40)

        # Length Slider
        length_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        length_row.pack(fill="x", pady=5)

        ctk.CTkLabel(length_row, text="PASSWORD LENGTH:", font=Theme.FONT_HEADER, text_color=Theme.TEXT_MAIN).pack(side="left")
        self.length_val_lbl = ctk.CTkLabel(length_row, text="18", font=Theme.FONT_MONO_BOLD, text_color=Theme.CYAN, width=35)
        self.length_val_lbl.pack(side="right")

        self.length_slider = ctk.CTkSlider(
            length_row,
            from_=6,
            to=64,
            number_of_steps=58,
            button_color=Theme.CYAN,
            button_hover_color=Theme.BLUE,
            progress_color=Theme.CYAN,
            command=self._on_slider_change
        )
        self.length_slider.set(18)
        self.length_slider.pack(side="right", fill="x", expand=True, padx=20)

        # Checkboxes for parameters
        cb_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        cb_frame.pack(fill="x", pady=15)

        self.var_upper = ctk.CTkCheckBox(cb_frame, text="A-Z (Uppercase)", font=Theme.FONT_BODY, text_color=Theme.TEXT_MAIN, fg_color=Theme.CYAN, hover_color=Theme.BLUE)
        self.var_upper.select()
        self.var_upper.grid(row=0, column=0, padx=15, pady=8, sticky="w")

        self.var_lower = ctk.CTkCheckBox(cb_frame, text="a-z (Lowercase)", font=Theme.FONT_BODY, text_color=Theme.TEXT_MAIN, fg_color=Theme.CYAN, hover_color=Theme.BLUE)
        self.var_lower.select()
        self.var_lower.grid(row=0, column=1, padx=15, pady=8, sticky="w")

        self.var_digits = ctk.CTkCheckBox(cb_frame, text="0-9 (Numbers)", font=Theme.FONT_BODY, text_color=Theme.TEXT_MAIN, fg_color=Theme.CYAN, hover_color=Theme.BLUE)
        self.var_digits.select()
        self.var_digits.grid(row=1, column=0, padx=15, pady=8, sticky="w")

        self.var_symbols = ctk.CTkCheckBox(cb_frame, text="!@#$ (Symbols)", font=Theme.FONT_BODY, text_color=Theme.TEXT_MAIN, fg_color=Theme.CYAN, hover_color=Theme.BLUE)
        self.var_symbols.select()
        self.var_symbols.grid(row=1, column=1, padx=15, pady=8, sticky="w")

        self.var_ambiguous = ctk.CTkCheckBox(cb_frame, text="Exclude Ambiguous (l, 1, O, 0)", font=Theme.FONT_BODY, text_color=Theme.TEXT_MAIN, fg_color=Theme.CYAN, hover_color=Theme.BLUE)
        self.var_ambiguous.grid(row=2, column=0, columnspan=2, padx=15, pady=8, sticky="w")

        # Action Buttons
        btn_row = ctk.CTkFrame(panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=40, pady=20)

        ctk.CTkButton(
            btn_row,
            text="⚡ RE-GENERATE",
            font=Theme.FONT_HEADER,
            fg_color=Theme.CYAN,
            text_color="#000000",
            hover_color=Theme.BLUE,
            height=40,
            command=self.generate_new_password
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="📋 COPY TO CLIPBOARD",
            font=Theme.FONT_HEADER,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.BLUE,
            height=40,
            command=self._copy_generated_password
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Initial generate
        self.generate_new_password()

    def _on_slider_change(self, val):
        self.length_val_lbl.configure(text=str(int(val)))
        self.generate_new_password()

    def generate_new_password(self):
        length = int(self.length_slider.get())
        pass_str = PasswordGenerator.generate(
            length=length,
            use_upper=bool(self.var_upper.get()),
            use_lower=bool(self.var_lower.get()),
            use_digits=bool(self.var_digits.get()),
            use_symbols=bool(self.var_symbols.get()),
            exclude_ambiguous=bool(self.var_ambiguous.get())
        )
        self.gen_password_lbl.delete(0, 'end')
        self.gen_password_lbl.insert(0, pass_str)

        label, entropy, color = PasswordGenerator.evaluate_strength(pass_str)
        progress_val = min(1.0, entropy / 100.0)

        self.strength_meter.configure(progress_color=color)
        self.strength_meter.set(progress_val)
        self.strength_desc_lbl.configure(
            text=f"SECURITY LEVEL: {label} ({entropy} bits entropy)",
            text_color=color
        )

    def _copy_generated_password(self):
        pwd = self.gen_password_lbl.get()
        if pwd:
            pyperclip.copy(pwd)
            self._start_clipboard_timer(30)

    # =================================================================
    # TAB 3: SECURITY AUDIT
    # =================================================================
    def _build_audit_tab(self):
        container = ctk.CTkFrame(self.tab_audit, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Summary Cards Row
        cards_row = ctk.CTkFrame(container, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 15))

        self.card_total = self._create_metric_card(cards_row, "TOTAL CREDENTIALS", "0", Theme.CYAN)
        self.card_weak = self._create_metric_card(cards_row, "WEAK PASSWORDS", "0", Theme.RED)
        self.card_reused = self._create_metric_card(cards_row, "REUSED PASSWORDS", "0", Theme.AMBER)
        self.card_score = self._create_metric_card(cards_row, "VAULT HEALTH", "100%", Theme.GREEN)

        # Audit Details Text Box / Panel
        audit_panel = ctk.CTkFrame(container, fg_color=Theme.PANEL_BG, border_color=Theme.PANEL_BORDER, border_width=1, corner_radius=10)
        audit_panel.pack(fill="both", expand=True)

        ctk.CTkLabel(
            audit_panel,
            text="REAL-TIME VAULT VULNERABILITY ANALYSIS",
            font=Theme.FONT_HEADER,
            text_color=Theme.CYAN
        ).pack(anchor="w", padx=20, pady=(15, 10))

        self.audit_textbox = ctk.CTkTextbox(
            audit_panel,
            font=Theme.FONT_MONO,
            fg_color=Theme.CARD_BG,
            text_color=Theme.TEXT_MAIN,
            corner_radius=8
        )
        self.audit_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        ctk.CTkButton(
            audit_panel,
            text="🔄 RUN VAULT AUDIT SCAN",
            font=Theme.FONT_HEADER,
            fg_color=Theme.CYAN,
            text_color="#000000",
            hover_color=Theme.BLUE,
            height=36,
            command=self.run_security_audit
        ).pack(pady=(0, 15))

    def _create_metric_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, fg_color=Theme.PANEL_BG, border_color=color, border_width=1, corner_radius=8, height=80)
        card.pack(side="left", fill="x", expand=True, padx=5)
        card.pack_propagate(False)

        ctk.CTkLabel(card, text=title, font=Theme.FONT_HUD, text_color=Theme.TEXT_MUTED).pack(pady=(12, 0))
        lbl_val = ctk.CTkLabel(card, text=value, font=("Segoe UI", 20, "bold"), text_color=color)
        lbl_val.pack(pady=(0, 5))
        return lbl_val

    def run_security_audit(self):
        """Performs vulnerability check on all vault credentials."""
        records = self.db.get_all_credentials()
        total = len(records)
        if total == 0:
            self.card_total.configure(text="0")
            self.card_weak.configure(text="0")
            self.card_reused.configure(text="0")
            self.card_score.configure(text="100%")
            self.audit_textbox.delete("1.0", "end")
            self.audit_textbox.insert("1.0", "[+] Vault is empty. No credentials analyzed.")
            return

        weak_list = []
        pass_counts = {}
        for r in records:
            pwd = r["password"]
            entropy = PasswordGenerator.calculate_entropy(pwd)
            if entropy < 50:
                weak_list.append((r["website"], r["username"], int(entropy)))
            pass_counts[pwd] = pass_counts.get(pwd, 0) + 1

        reused_count = sum(count for count in pass_counts.values() if count > 1)

        self.card_total.configure(text=str(total))
        self.card_weak.configure(text=str(len(weak_list)))
        self.card_reused.configure(text=str(reused_count))

        health_percentage = max(0, 100 - (len(weak_list) * 15 + reused_count * 10))
        health_color = Theme.GREEN if health_percentage > 80 else (Theme.AMBER if health_percentage > 50 else Theme.RED)
        self.card_score.configure(text=f"{health_percentage}%", text_color=health_color)

        self.audit_textbox.delete("1.0", "end")
        report = []
        report.append("==========================================================================")
        report.append("                    CYBERVAULT VULNERABILITY AUDIT REPORT                  ")
        report.append("==========================================================================")
        report.append(f"[+] Total Accounts Scanned: {total}")
        report.append(f"[+] Overall Vault Security Index: {health_percentage}%")
        report.append(f"[+] Encryption Protocol: AES-256 (Fernet) + PBKDF2 Key Derivation (200k iter)")
        report.append("--------------------------------------------------------------------------\n")

        if weak_list:
            report.append("[!] WEAK PASSWORDS DETECTED (Low Entropy < 50 bits):")
            for web, user, ent in weak_list:
                report.append(f"    - {web} ({user}) -> Entropy: {ent} bits [RECOMMENDATION: Regenerate]")
            report.append("")

        if reused_count > 0:
            report.append("[!] REUSED PASSWORDS DETECTED across multiple accounts:")
            for pwd, count in pass_counts.items():
                if count > 1:
                    reused_sites = [r["website"] for r in records if r["password"] == pwd]
                    report.append(f"    - Reused across {count} services: {', '.join(reused_sites)}")
            report.append("")

        if not weak_list and reused_count == 0:
            report.append("[✓] EXCELLENT SECURITY POSTURE! No weak or reused passwords detected.")

        self.audit_textbox.insert("1.0", "\n".join(report))

    # =================================================================
    # TAB 4: BACKUPS & SETTINGS
    # =================================================================
    def _build_settings_tab(self):
        panel = ctk.CTkScrollableFrame(self.tab_settings, fg_color=Theme.PANEL_BG, border_color=Theme.PANEL_BORDER, border_width=1, corner_radius=10)
        panel.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(panel, text="BACKUP & VAULT MANAGEMENT", font=Theme.FONT_TITLE, text_color=Theme.CYAN).pack(pady=(20, 5))
        ctk.CTkLabel(panel, text="Export or restore encrypted backups to prevent data loss.", font=Theme.FONT_HUD, text_color=Theme.TEXT_MUTED).pack(pady=(0, 20))

        # Encrypted Backup Box
        enc_box = ctk.CTkFrame(panel, fg_color=Theme.CARD_BG, border_color=Theme.CYAN, border_width=1, corner_radius=8)
        enc_box.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(enc_box, text="🔒 ENCRYPTED BACKUP (.json)", font=Theme.FONT_HEADER, text_color=Theme.CYAN).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(enc_box, text="Backs up all credentials with a custom master backup password.", font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=15, pady=(0, 10))

        enc_btn_row = ctk.CTkFrame(enc_box, fg_color="transparent")
        enc_btn_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            enc_btn_row,
            text="EXPORT ENCRYPTED BACKUP",
            font=Theme.FONT_HUD,
            fg_color=Theme.CYAN,
            text_color="#000000",
            hover_color=Theme.BLUE,
            height=36,
            command=self._export_encrypted_backup
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            enc_btn_row,
            text="RESTORE ENCRYPTED BACKUP",
            font=Theme.FONT_HUD,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.CYAN,
            height=36,
            command=self._import_encrypted_backup
        ).pack(side="left")

        # Multi-Device Portable Vault Box
        sync_box = ctk.CTkFrame(panel, fg_color=Theme.CARD_BG, border_color=Theme.GREEN, border_width=1, corner_radius=8)
        sync_box.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(sync_box, text="🌐 MULTI-DEVICE PORTABLE VAULT SYNC", font=Theme.FONT_HEADER, text_color=Theme.GREEN).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(sync_box, text="Sync your encrypted vault across multiple PCs, laptops, cloud drives (OneDrive/Google Drive/Dropbox), or USB sticks.", font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=15, pady=(0, 10))

        sync_btn_row = ctk.CTkFrame(sync_box, fg_color="transparent")
        sync_btn_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            sync_btn_row,
            text="EXPORT PORTABLE VAULT (.cybervault)",
            font=Theme.FONT_HUD,
            fg_color=Theme.GREEN,
            text_color="#000000",
            hover_color=Theme.CYAN,
            height=36,
            command=self._export_portable_vault
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            sync_btn_row,
            text="IMPORT PORTABLE VAULT (.cybervault)",
            font=Theme.FONT_HUD,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.GREEN,
            height=36,
            command=self._import_portable_vault
        ).pack(side="left")

        # CSV Box
        csv_box = ctk.CTkFrame(panel, fg_color=Theme.CARD_BG, border_color=Theme.PANEL_BORDER, border_width=1, corner_radius=8)
        csv_box.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(csv_box, text="📄 UNENCRYPTED CSV IMPORT / EXPORT", font=Theme.FONT_HEADER, text_color=Theme.AMBER).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(csv_box, text="Warning: Plain CSV exports contain unencrypted credentials!", font=Theme.FONT_BODY, text_color=Theme.RED).pack(anchor="w", padx=15, pady=(0, 10))

        csv_btn_row = ctk.CTkFrame(csv_box, fg_color="transparent")
        csv_btn_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            csv_btn_row,
            text="EXPORT CSV",
            font=Theme.FONT_HUD,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.AMBER,
            height=36,
            command=self._export_csv
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            csv_btn_row,
            text="IMPORT CSV",
            font=Theme.FONT_HUD,
            fg_color=Theme.CARD_BG,
            hover_color=Theme.BLUE,
            height=36,
            command=self._import_csv
        ).pack(side="left")

    # =================================================================
    # ACTIONS & HELPERS
    # =================================================================
    def _handle_lock(self):
        self.crypto.lock_vault()
        self.on_lock()

    def _start_clipboard_timer(self, seconds: int = 30):
        if self._clipboard_timer_id:
            self.after_cancel(self._clipboard_timer_id)
        self._clipboard_seconds_left = seconds
        self._update_clipboard_countdown()

    def _update_clipboard_countdown(self):
        if self._clipboard_seconds_left > 0:
            self.clipboard_status_lbl.configure(text=f"📋 CLIPBOARD CLEARS IN {self._clipboard_seconds_left}s")
            self._clipboard_seconds_left -= 1
            self._clipboard_timer_id = self.after(1000, self._update_clipboard_countdown)
        else:
            pyperclip.copy("")
            self.clipboard_status_lbl.configure(text="📋 CLIPBOARD CLEARED", text_color=Theme.GREEN)

    def _copy_selected_username(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a credential row first.")
            return
        vals = self.tree.item(selected[0], "values")
        username = vals[2]
        pyperclip.copy(username)
        messagebox.showinfo("Copied", f"Username '{username}' copied to clipboard.")

    def _copy_selected_password(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a credential row first.")
            return
        rec_id = self.tree.item(selected[0], "values")[0]
        all_recs = self.db.get_all_credentials()
        match = next((r for r in all_recs if str(r["id"]) == str(rec_id)), None)
        if match:
            pyperclip.copy(match["password"])
            self._start_clipboard_timer(30)
            messagebox.showinfo("Copied", "Password copied to clipboard!\n(Auto-clears in 30 seconds)")

    def _view_selected_credential(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a credential row first.")
            return
        rec_id = self.tree.item(selected[0], "values")[0]
        all_recs = self.db.get_all_credentials()
        match = next((r for r in all_recs if str(r["id"]) == str(rec_id)), None)
        if match:
            self._open_edit_credential_dialog(match)

    def _delete_selected_credential(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a credential row first.")
            return
        rec_id = self.tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete credential #{rec_id}?"):
            self.db.delete_credential(int(rec_id))
            self.refresh_vault_list()

    def _open_add_credential_dialog(self):
        self._show_credential_modal(title="ADD NEW CREDENTIAL", is_edit=False)

    def _open_edit_credential_dialog(self, record: Dict):
        self._show_credential_modal(title="EDIT CREDENTIAL", is_edit=True, record=record)

    def _show_credential_modal(self, title: str, is_edit: bool = False, record: Optional[Dict] = None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("450x550")
        dialog.configure(fg_color=Theme.BG_DARK)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=title, font=Theme.FONT_TITLE, text_color=Theme.CYAN).pack(pady=(20, 15))

        # Fields
        ctk.CTkLabel(dialog, text="WEBSITE / SERVICE:", font=Theme.FONT_HUD, text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=30, pady=(5, 2))
        ent_web = ctk.CTkEntry(dialog, font=Theme.FONT_BODY, fg_color=Theme.CARD_BG, text_color=Theme.TEXT_MAIN, height=36)
        ent_web.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkLabel(dialog, text="USERNAME / EMAIL:", font=Theme.FONT_HUD, text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=30, pady=(5, 2))
        ent_user = ctk.CTkEntry(dialog, font=Theme.FONT_BODY, fg_color=Theme.CARD_BG, text_color=Theme.TEXT_MAIN, height=36)
        ent_user.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkLabel(dialog, text="PASSWORD:", font=Theme.FONT_HUD, text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=30, pady=(5, 2))
        pass_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        pass_frame.pack(fill="x", padx=30, pady=(0, 10))

        ent_pass = ctk.CTkEntry(pass_frame, font=Theme.FONT_MONO, fg_color=Theme.CARD_BG, text_color=Theme.TEXT_MAIN, height=36, show="*")
        ent_pass.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def toggle_show():
            if ent_pass.cget("show") == "*":
                ent_pass.configure(show="")
            else:
                ent_pass.configure(show="*")

        ctk.CTkButton(pass_frame, text="👁️", width=36, height=36, fg_color=Theme.CARD_BG, command=toggle_show).pack(side="right")

        ctk.CTkLabel(dialog, text="CATEGORY:", font=Theme.FONT_HUD, text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=30, pady=(5, 2))
        ent_cat = ctk.CTkComboBox(dialog, values=["General", "Social Media", "Banking / Finance", "Work", "Personal", "Other"], font=Theme.FONT_BODY, fg_color=Theme.CARD_BG, text_color=Theme.TEXT_MAIN, height=36)
        ent_cat.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkLabel(dialog, text="NOTES / EXTRA:", font=Theme.FONT_HUD, text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=30, pady=(5, 2))
        ent_notes = ctk.CTkEntry(dialog, font=Theme.FONT_BODY, fg_color=Theme.CARD_BG, text_color=Theme.TEXT_MAIN, height=36)
        ent_notes.pack(fill="x", padx=30, pady=(0, 15))

        if is_edit and record:
            ent_web.insert(0, record["website"])
            ent_user.insert(0, record["username"])
            ent_pass.insert(0, record["password"])
            ent_cat.set(record.get("category", "General"))
            ent_notes.insert(0, record.get("notes", ""))

        def save_action():
            web = ent_web.get().strip()
            usr = ent_user.get().strip()
            pwd = ent_pass.get().strip()
            cat = ent_cat.get().strip() or "General"
            nts = ent_notes.get().strip()

            if not web or not usr or not pwd:
                messagebox.showwarning("Validation Warning", "Website, Username and Password fields are required.")
                return

            if is_edit and record:
                self.db.update_credential(record["id"], web, usr, pwd, cat, nts)
            else:
                self.db.add_credential(web, usr, pwd, cat, nts)

            self.refresh_vault_list()
            dialog.destroy()

        ctk.CTkButton(
            dialog,
            text="SAVE CREDENTIAL" if not is_edit else "UPDATE CREDENTIAL",
            font=Theme.FONT_HEADER,
            fg_color=Theme.CYAN,
            text_color="#000000",
            hover_color=Theme.BLUE,
            height=40,
            command=save_action
        ).pack(fill="x", padx=30, pady=10)

    def _export_encrypted_backup(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Encrypted Vault Backup", "*.json")])
        if not file_path:
            return
        pwd = ctk.CTkInputDialog(text="Enter a master backup password to encrypt this file:", title="Backup Encryption Password").get_input()
        if not pwd:
            return
        try:
            BackupManager.export_encrypted_backup(file_path, pwd, self.db)
            messagebox.showinfo("Backup Complete", "Encrypted backup saved successfully!")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _import_encrypted_backup(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Vault Backup", "*.json")])
        if not file_path:
            return
        pwd = ctk.CTkInputDialog(text="Enter the backup password used to encrypt this file:", title="Decrypt Backup File").get_input()
        if not pwd:
            return
        try:
            count = BackupManager.import_encrypted_backup(file_path, pwd, self.db)
            self.refresh_vault_list()
            messagebox.showinfo("Import Successful", f"Successfully restored {count} credentials into vault.")
        except Exception as e:
            messagebox.showerror("Import Failed", f"Invalid backup password or corrupted backup file.\n{str(e)}")

    def _export_csv(self):
        if not messagebox.askyesno("Security Warning", "CSV files store passwords in UNENCRYPTED plain text.\nAre you sure you want to export unencrypted CSV?"):
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
        if file_path:
            count = BackupManager.export_csv(file_path, self.db)
            messagebox.showinfo("Export Complete", f"Exported {count} records to CSV.")

    def _import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV File", "*.csv")])
        if file_path:
            try:
                count = BackupManager.import_csv(file_path, self.db)
                self.refresh_vault_list()
                messagebox.showinfo("Import Complete", f"Imported {count} records from CSV.")
            except Exception as e:
                messagebox.showerror("Import Failed", str(e))

    def _export_portable_vault(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".cybervault", filetypes=[("CyberVault Portable Bundle", "*.cybervault")])
        if not file_path:
            return
        pwd = ctk.CTkInputDialog(text="Enter Master Password or custom password to encrypt portable vault bundle:", title="Portable Vault Encryption").get_input()
        if not pwd:
            return
        try:
            BackupManager.export_portable_vault(file_path, pwd, self.db)
            messagebox.showinfo("Portable Export Complete", f"Portable vault exported to '{os.path.basename(file_path)}'!\n\nYou can now copy this bundle to any device and import it.")
        except Exception as e:
            messagebox.showerror("Portable Export Failed", str(e))

    def _import_portable_vault(self):
        file_path = filedialog.askopenfilename(filetypes=[("CyberVault Portable Bundle", "*.cybervault")])
        if not file_path:
            return
        pwd = ctk.CTkInputDialog(text="Enter the Master Password or bundle password to decrypt and import vault:", title="Decrypt Portable Vault").get_input()
        if not pwd:
            return
        try:
            count = BackupManager.import_portable_vault(file_path, pwd, self.db)
            self.refresh_vault_list()
            messagebox.showinfo("Portable Import Successful", f"Successfully synced {count} credentials into your vault!")
        except Exception as e:
            messagebox.showerror("Portable Import Failed", f"Failed to decrypt portable vault bundle.\n{str(e)}")
