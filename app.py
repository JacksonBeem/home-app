"""app.py

Main Home App shell (dashboard wrapper).

This file stays intentionally separate from the pantry feature module.
The pantry module lives in pantry_app.py and can still be run standalone.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ui_style import STYLE_CONFIG, apply_global_style

# from database import init_db_schema
from pantryapp.pantry_app import PantryPage
from choresapp.chores_app import ChoresPage
from cookingapp.cooking_app import CookingPage
from familyapp.family_app import FamilyPage


class HomeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Welcome Home")
        self.geometry("1024x600")
        apply_global_style(self)

        # Keep the same modern styling palette as the pantry module.
        self._setup_style()

        # Pages
        self._home_page = HomeDashboard(self, on_open=self._open_page)
        self._pantry_page = PantryPage(self, on_home=self.show_home)
        self._chores_page = ChoresPage(self, on_home=self.show_home)
        try:
            self._cooking_page = CookingPage(self, on_home=self.show_home)
        except ImportError:
            self._cooking_page = PlaceholderPage(self, title="Cooking", subtitle="Recipe management (unavailable)")
        #self._chores_page = ChoresPage(self, on_open=self._open_page)
        self._family_page = FamilyPage(self, on_home=self.show_home)
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

        # self.configure(bg=self.STYLE_CONFIG["bg_main"])  # Not supported for ttk widgets

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
        self._home_page.refresh_alerts() 
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
        from ui_style import STYLE_CONFIG
        super().__init__(master, padding=16)
        self.on_open = on_open
        self._weather_var = tk.StringVar(value="Loading weather...")
        self._build()
        self._fetch_weather_async()

    def _build(self) -> None:
        # Header
        header = ttk.Frame(self)
        header.pack(side=tk.TOP, fill=tk.X)
        title = ttk.Label(header, text="Welcome Home", style="HomeTitle.TLabel")
        title.pack(side=tk.LEFT, anchor="w")
        subtitle = ttk.Label(header, text="Tap a tile to open a module", style="HomeSub.TLabel")
        subtitle.pack(side=tk.LEFT, anchor="w", padx=(16, 0), pady=(10, 0))

        # --- Main Layout Container ---
        main_content = ttk.Frame(self)
        main_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(22, 0))

        # LEFT SIDE: Navigation Tiles
        tiles = ttk.Frame(main_content, style="Card.TFrame", padding=18)
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

        # RIGHT SIDE: Alert List
        alert_frame = ttk.LabelFrame(main_content, text="Chore Alerts", padding=10)
        alert_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(30, 0))

        # Listbox for alerts
        self.alert_list = tk.Listbox(alert_frame, font=("Segoe UI", 12), borderwidth=0, highlightthickness=0)
        self.alert_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the alert list
        scroller = ttk.Scrollbar(alert_frame, orient=tk.VERTICAL, command=self.alert_list.yview)
        scroller.pack(side=tk.RIGHT, fill=tk.Y)
        self.alert_list.config(yscrollcommand=scroller.set)

        # Weather display at the bottom
        weather_frame = ttk.Frame(self)
        weather_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        ttk.Label(weather_frame, textvariable=self._weather_var, font=("Segoe UI", 14), anchor="center").pack(fill=tk.X)

    def _fetch_weather_async(self):
        import threading
        threading.Thread(target=self._fetch_weather, daemon=True).start()

    def _fetch_weather(self):
        import requests
        try:
            # --- CONFIGURE YOUR CITY AND API KEY HERE ---
            CITY = "Sterling Heights,US"
            API_KEY = "placeholder"  # Replace with your OpenWeatherMap API key
            url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=imperial"
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description'].capitalize()
            city = data['name']
            weather_str = f"Weather in {city}: {temp:.0f}°F, {desc}"
        except Exception as e:
            weather_str = f"Weather unavailable."
        self._weather_var.set(weather_str)

    def refresh_alerts(self):
        """Fetches chores and filters for anything NOT 'Daily'."""
        self.alert_list.delete(0, tk.END)
        try:
            # Local import to prevent circular dependency
            from choresapp.chores_model import get_all_chores
            chores = get_all_chores()
            
            for c in chores:
                # Only show if frequency is NOT Daily (Weekly, Monthly, etc.)
                if c.frequency and "daily" not in c.frequency.lower():
                    status = f"🔔 {c.description} ({c.frequency})"
                    self.alert_list.insert(tk.END, status)
                    
                    # Highlight Priority 1 (Red) in the alert list too
                    if c.priority == 1:
                        self.alert_list.itemconfig(tk.END, foreground="red")
        except Exception as e:
            self.alert_list.insert(tk.END, "No alerts available.")

# class ChoresPage(ttk.Frame):
#     def __init__(self, master: tk.Misc, *, on_open):
#         super().__init__(master)
#         self.on_open = on_open
#         self._build()
#     def _build(self) -> None:
#         # Header
#         header = ttk.Frame(self)
#         header.pack(side=tk.TOP, fill=tk.X)

#         title = ttk.Label(header, text="House Chores", style="HomeTitle.TLabel")
#         title.pack(side=tk.LEFT, anchor="w")

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

    def _build(self) -> None:
        from banner import TopBanner
        TopBanner(self, title="Welcome Home").pack(side=tk.TOP, fill=tk.X)
        subtitle = ttk.Label(self, text="Tap a tile to open a module", style="HomeSub.TLabel")
        subtitle.pack(side=tk.TOP, anchor="w", padx=(18, 0), pady=(0, 12))

        # Main navigation buttons
        nav = ttk.Frame(self)
        nav.pack(side=tk.TOP, pady=40)
        btns = [
            ("Pantry", lambda: self.on_open("pantry")),
            ("Chores", lambda: self.on_open("chores")),
            ("Cooking", lambda: self.on_open("cooking")),
            ("Family", lambda: self.on_open("family")),
        ]
        for i, (label, cmd) in enumerate(btns):
            b = ttk.Button(nav, text=label, command=cmd, width=16)
            b.grid(row=0, column=i, padx=16, pady=8)

# Restore _go_home method and main entry point
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