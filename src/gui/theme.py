import customtkinter as ctk

class Theme:
    """
    Sci-Fi Cyberpunk Theme Palette & Styling Specifications.
    """
    # System theme initialization
    @staticmethod
    def apply_theme():
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

    # Sci-Fi Color Palette
    BG_DARK = "#090C15"          # Deep Space Void
    PANEL_BG = "#101625"         # Holographic Panel Deck
    PANEL_BORDER = "#1A243B"     # Cyberpunk Grid Line
    CARD_BG = "#161E31"          # Tactical Card Fill

    # Neon Sci-Fi Accents
    CYAN = "#00F0FF"             # Cyber Cyan (Primary Accent)
    BLUE = "#0066FF"             # Quantum Blue
    GREEN = "#00FF66"            # Holo Green (Secure)
    AMBER = "#FFB800"            # Solar Gold (Warning)
    RED = "#FF2A6D"              # Plasma Red (Danger/Weak)
    PURPLE = "#A855F7"           # Void Purple

    # Typography / HUD Text
    TEXT_MAIN = "#E6F4FF"        # High-Contrast Holo Text
    TEXT_SECONDARY = "#8FA3BF"   # Sub-label Grey
    TEXT_MUTED = "#4A5B73"       # Faded HUD Label

    # Font definitions
    FONT_TITLE = ("Segoe UI", 20, "bold")
    FONT_HEADER = ("Segoe UI", 15, "bold")
    FONT_BODY = ("Segoe UI", 12)
    FONT_MONO = ("Consolas", 12)
    FONT_MONO_BOLD = ("Consolas", 13, "bold")
    FONT_HUD = ("Segoe UI", 10, "bold")
