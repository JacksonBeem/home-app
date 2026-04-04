# banner.py
# Reusable top banner/bar for all pages

import tkinter as tk
from tkinter import ttk
from ui_style import STYLE_CONFIG

class TopBanner(ttk.Frame):
    def __init__(self, master, title, on_home=None, right_widget=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(style="Banner.TFrame")
        self._build(title, on_home, right_widget)

    def _build(self, title, on_home, right_widget):
        style = ttk.Style(self)
        style.configure("Banner.TFrame", background=STYLE_CONFIG["banner_bg"])
        style.configure("BannerTitle.TLabel", font=(STYLE_CONFIG["font_bold"], STYLE_CONFIG["font_title"]), foreground=STYLE_CONFIG["banner_fg"], background=STYLE_CONFIG["banner_bg"])
        style.configure("BannerShadow.TFrame", background=STYLE_CONFIG["banner_shadow"])
        style.configure("BannerHome.TButton", font=(STYLE_CONFIG["font"], STYLE_CONFIG["font_size"]), background=STYLE_CONFIG["banner_bg"], foreground=STYLE_CONFIG["accent_blue"]) 

        # Banner shadow (bottom border)
        shadow = ttk.Frame(self, style="BannerShadow.TFrame", height=2)
        shadow.pack(side=tk.BOTTOM, fill=tk.X)

        # Main banner row
        row = ttk.Frame(self, style="Banner.TFrame")
        row.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)

        if on_home:
            home_btn = ttk.Button(row, text="\u2190 Home", style="BannerHome.TButton", command=on_home)
            home_btn.pack(side=tk.LEFT, padx=(12, 8), pady=6)
        ttk.Label(row, text=title, style="BannerTitle.TLabel").pack(side=tk.LEFT, padx=(8, 0), pady=6)
        if right_widget:
            right_widget.pack(side=tk.RIGHT, padx=(0, 12), pady=6)
