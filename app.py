"""app.py

Main Home App shell (dashboard wrapper).

This file stays intentionally separate from the pantry feature module.
The pantry module lives in pantry_app.py and can still be run standalone.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk

# from database import init_db_schema
from pantryapp.pantry_app import PantryPage
from choresapp.chores_app import ChoresPage
from cookingapp.cooking_app import CookingPage


class HomeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Welcome Home")
        self.geometry("1024x600")
        self.option_add("*Font", ("Segoe UI", 14))

        # Keep the same modern styling palette as the pantry module.
        self._setup_style()

        # Pages
        self._home_page = HomeDashboard(self, on_open=self._open_page)
        self._pantry_page = PantryPage(self, on_home=self.show_home)
        self._cooking_page = PlaceholderPage(self, title="Cooking", subtitle="Recipe management (coming soon)")
        self._chores_page = ChoresPage(self, on_home=self.show_home)
        try:
            self._cooking_page = CookingPage(self, on_home=self.show_home)
        except ImportError:
            self._cooking_page = PlaceholderPage(self, title="Cooking", subtitle="Recipe management (unavailable)")
        self._family_page = PlaceholderPage(self, title="Family", subtitle="Members & preferences (coming soon)")
        self._new_page = PlaceholderPage(self, title="Add", subtitle="Create a new module (coming soon)")

        self.show_home()

    # --------- Styling ---------

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.STYLE_CONFIG = {
            "bg_main": "#f7f9fc",
            "bg_panel": "#ffffff",
            "accent_blue": "#4a90e2",
            "accent_blue_dark": "#357ab8",
            "text_main": "#1f2933",
            "text_muted": "#6b7b8c",
            "stroke": "#d0d7e2",
        }

        self.configure(bg=self.STYLE_CONFIG["bg_main"])

        bg_main = self.STYLE_CONFIG["bg_main"]
        bg_panel = self.STYLE_CONFIG["bg_panel"]
        text_main = self.STYLE_CONFIG["text_main"]
        text_muted = self.STYLE_CONFIG["text_muted"]
        accent = self.STYLE_CONFIG["accent_blue"]
        accent_dark = self.STYLE_CONFIG["accent_blue_dark"]

        style.configure("TFrame", background=bg_main)
        style.configure("Card.TFrame", background=bg_panel, relief="flat", borderwidth=0)
        style.configure("TLabel", background=bg_main, foreground=text_main)

        style.configure(
            "HomeTitle.TLabel",
            font=("Segoe UI Semibold", 30),
            background=bg_main,
            foreground=text_main,
            padding=(0, 0, 0, 4),
        )
        style.configure(
            "HomeSub.TLabel",
            font=("Segoe UI", 13),
            background=bg_main,
            foreground=text_muted,
        )

        # Tile button style (flat card-like)
        style.configure(
            "Tile.TButton",
            font=("Segoe UI Semibold", 18),
            padding=(18, 18),
            background=bg_panel,
            foreground=text_main,
            borderwidth=1,
            focusthickness=0,
            relief="solid",
        )
        style.map(
            "Tile.TButton",
            background=[("active", "#eef5ff")],
            relief=[("pressed", "solid")],
        )

        style.configure(
            "TilePlus.TButton",
            font=("Segoe UI Semibold", 26),
            padding=(18, 18),
            background=bg_panel,
            foreground=accent,
            borderwidth=1,
            focusthickness=0,
            relief="solid",
        )
        style.map(
            "TilePlus.TButton",
            background=[("active", "#eef5ff")],
            foreground=[("active", accent_dark)],
        )

    # --------- Navigation ---------

    def _hide_all_pages(self) -> None:
        for page in (
            self._home_page,
            self._pantry_page,
            self._cooking_page,
            self._chores_page,
            self._family_page,
            self._new_page,
        ):
            page.pack_forget()

        # Make sure modules can clean up bindings if needed.
        try:
            self._pantry_page.deactivate()
        except Exception:
            pass

    def show_home(self) -> None:
        self._hide_all_pages()
        self._home_page.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=26, pady=22)

    def _open_page(self, key: str) -> None:
        self._hide_all_pages()

        if key == "pantry":
            self._pantry_page.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=18)
            self._pantry_page.activate()
        elif key == "cooking":
            self._cooking_page.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=18)
        elif key == "chores":
            self._chores_page.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=18)
        elif key == "family":
            self._family_page.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=18)
        elif key == "new":
            self._new_page.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=18)
        else:
            self.show_home()


class HomeDashboard(ttk.Frame):
    # Main tile dashboard.

    def __init__(self, master: tk.Misc, *, on_open):
        super().__init__(master)
        self.on_open = on_open
        self._build()

    def _build(self) -> None:
        # Header
        header = ttk.Frame(self)
        header.pack(side=tk.TOP, fill=tk.X)

        title = ttk.Label(header, text="Welcome Home", style="HomeTitle.TLabel")
        title.pack(side=tk.LEFT, anchor="w")

        subtitle = ttk.Label(
            header,
            text="Tap a tile to open a module",
            style="HomeSub.TLabel",
        )
        subtitle.pack(side=tk.LEFT, anchor="w", padx=(16, 0), pady=(10, 0))

        # Tiles area
        tiles_outer = ttk.Frame(self)
        tiles_outer.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(22, 0))

        tiles = ttk.Frame(tiles_outer, style="Card.TFrame", padding=18)
        tiles.pack(side=tk.LEFT, anchor="n")

        # Make tiles consistent size
        tile_w = 16
        tile_h = 4

        def tile(text: str, key: str, style: str = "Tile.TButton"):
            return ttk.Button(
                tiles,
                text=text,
                style=style,
                width=tile_w,
                command=lambda: self.on_open(key),
            )

        btn_cooking = tile("Cooking", "cooking")
        btn_pantry = tile("Pantry", "pantry")
        btn_family = tile("Family", "family")
        btn_chores = tile("Chores", "chores")
        btn_plus = tile("+", "new", style="TilePlus.TButton")

        # Grid like the sketch
        btn_cooking.grid(row=0, column=0, padx=14, pady=14, ipadx=8, ipady=tile_h)
        btn_pantry.grid(row=0, column=1, padx=14, pady=14, ipadx=8, ipady=tile_h)
        btn_family.grid(row=1, column=0, padx=14, pady=14, ipadx=8, ipady=tile_h)
        btn_chores.grid(row=1, column=1, padx=14, pady=14, ipadx=8, ipady=tile_h)
        btn_plus.grid(row=2, column=0, padx=14, pady=(14, 0), ipadx=8, ipady=tile_h)

        # Spacer to preserve the empty bottom-right tile area like your sketch
        spacer = ttk.Frame(tiles, width=1)
        spacer.grid(row=2, column=1, padx=14, pady=(14, 0), sticky="nsew")

class PlaceholderPage(ttk.Frame):
    def __init__(self, master: tk.Misc, *, title: str, subtitle: str):
        super().__init__(master, padding=20)
        self.title = title
        self.subtitle = subtitle
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X)

        back = ttk.Button(top, text="\u2190 Home", style="TopNav.TButton", command=self._go_home)
        back.pack(side=tk.LEFT, padx=(0, 12))

        t = ttk.Label(top, text=self.title, style="Title.TLabel")
        t.pack(side=tk.LEFT)

        body = ttk.Frame(self, style="Card.TFrame", padding=18)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(18, 0))

        lbl = ttk.Label(body, text=self.subtitle, style="Filter.TLabel")
        lbl.pack(side=tk.TOP, anchor="w")

    def _go_home(self) -> None:
        root = self.winfo_toplevel()
        if hasattr(root, "show_home"):
            root.show_home()


def main() -> None:
    #init_db_schema()
    app = HomeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
