# ui_style.py
# Global UI style configuration for the Home App


STYLE_CONFIG = {
    "bg_main": "#f7f9fc",
    "bg_panel": "#ffffff",
    "accent_blue": "#4a90e2",
    "accent_blue_dark": "#357ab8",
    "accent_yellow": "#ffe082",
    "accent_red": "#e57373",
    "accent_red_dark": "#c62828",
    "text_main": "#1f2933",
    "text_muted": "#6b7b8c",
    "stroke": "#d0d7e2",
    "banner_bg": "#ffffff",
    "banner_fg": "#1f2933",
    "banner_shadow": "#e0e6ed",
    "font": "Segoe UI",
    "font_size": 15,
    "font_title": 22,
    "font_bold": "Segoe UI Semibold",
    "card_radius": 10,
    "card_shadow": "#e0e6ed",
    "button_radius": 8,
    "button_bg": "#4a90e2",
    "button_fg": "#ffffff",
    "button_hover": "#357ab8",
    "button_secondary_bg": "#f0f1f5",
    "button_secondary_fg": "#4a90e2",
    "button_secondary_hover": "#e3e8f0",
    "button_font": "Segoe UI",
    "button_font_size": 15,
    "list_row_height": 36,
    "list_alt_bg": "#f0f4fa",
    "list_selected_bg": "#d8e8ff",
    "list_selected_fg": "#1f2933",
    "list_header_bg": "#e6f0fb",
    "list_header_fg": "#1f2933",
}

def apply_global_style(root):
    """
    Apply global font and background to the root window, and set up button/list styles.
    """
    root.option_add("*Font", (STYLE_CONFIG["font"], STYLE_CONFIG["font_size"]))
    # Button styles
    style = ttk.Style(root)
    style.configure("Accent.TButton",
        font=(STYLE_CONFIG["button_font"], STYLE_CONFIG["button_font_size"]),
        background=STYLE_CONFIG["button_bg"],
        foreground=STYLE_CONFIG["button_fg"],
        borderwidth=0,
        focusthickness=0,
        padding=(14, 8),
        relief="flat",
    )
    style.map("Accent.TButton",
        background=[("active", STYLE_CONFIG["button_hover"]), ("!active", STYLE_CONFIG["button_bg"])],
        foreground=[("active", STYLE_CONFIG["button_fg"])]
    )
    style.configure("Secondary.TButton",
        font=(STYLE_CONFIG["button_font"], STYLE_CONFIG["button_font_size"]),
        background=STYLE_CONFIG["button_secondary_bg"],
        foreground=STYLE_CONFIG["button_secondary_fg"],
        borderwidth=0,
        focusthickness=0,
        padding=(14, 8),
        relief="flat",
    )
    style.map("Secondary.TButton",
        background=[("active", STYLE_CONFIG["button_secondary_hover"]), ("!active", STYLE_CONFIG["button_secondary_bg"])],
        foreground=[("active", STYLE_CONFIG["button_secondary_fg"])]
    )
    # List/Treeview styles
    style.configure("Custom.Treeview",
        font=(STYLE_CONFIG["font"], 18),
        rowheight=STYLE_CONFIG["list_row_height"],
        background=STYLE_CONFIG["bg_panel"],
        fieldbackground=STYLE_CONFIG["bg_panel"],
        foreground=STYLE_CONFIG["text_main"],
        bordercolor=STYLE_CONFIG["stroke"],
        borderwidth=1,
    )
    style.map("Custom.Treeview",
        background=[("selected", STYLE_CONFIG["list_selected_bg"]), ("!selected", STYLE_CONFIG["bg_panel"])],
        foreground=[("selected", STYLE_CONFIG["list_selected_fg"]), ("!selected", STYLE_CONFIG["text_main"])]
    )
    style.configure("Custom.Treeview.Heading",
        font=(STYLE_CONFIG["font_bold"], STYLE_CONFIG["font_size"]),
        background=STYLE_CONFIG["list_header_bg"],
        foreground=STYLE_CONFIG["list_header_fg"],
        relief="flat",
    )

def apply_global_style(root):
    """
    Apply global font and background to the root window.
    """
    root.option_add("*Font", (STYLE_CONFIG["font"], STYLE_CONFIG["font_size"]))
    root.configure(bg=STYLE_CONFIG["bg_main"])
