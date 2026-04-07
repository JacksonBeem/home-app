"""app.py

Main Home App shell (dashboard wrapper).

This file stays intentionally separate from the pantry feature module.
The pantry module lives in pantry_app.py and can still be run standalone.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

# from database import init_db_schema
from pantryapp.pantry_app import PantryPage
from choresapp.chores_app import ChoresPage
from cookingapp.cooking_app import CookingPage
from assistantapp.openrouter_agent import ask_pantry_assistant
from assistantapp.speech_to_text import record_and_transcribe


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
        self._chores_page = ChoresPage(self, on_home=self.show_home)
        try:
            self._cooking_page = CookingPage(self, on_home=self.show_home)
        except ImportError:
            self._cooking_page = PlaceholderPage(self, title="Cooking", subtitle="Recipe management (unavailable)")
        #self._chores_page = ChoresPage(self, on_open=self._open_page)
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
        self.assistant_output: scrolledtext.ScrolledText | None = None
        self.assistant_entry: ttk.Entry | None = None
        self.assistant_send_btn: ttk.Button | None = None
        self.assistant_mic_btn: ttk.Button | None = None
        self._mic_busy = False
        self._mic_request_id = 0
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

        # Pantry Assistant Chat
        assistant = ttk.Frame(tiles_outer, style="Card.TFrame", padding=14)
        assistant.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 0))

        assistant_title = ttk.Label(
            assistant,
            text="Pantry Assistant",
            style="HomeSub.TLabel",
        )
        assistant_title.pack(anchor="w", pady=(0, 8))

        self.assistant_output = scrolledtext.ScrolledText(
            assistant,
            wrap=tk.WORD,
            height=16,
            state="disabled",
        )
        self.assistant_output.pack(fill=tk.BOTH, expand=True)

        entry_row = ttk.Frame(assistant)
        entry_row.pack(fill=tk.X, pady=(8, 0))

        self.assistant_entry = ttk.Entry(entry_row)
        self.assistant_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.assistant_entry.bind("<Return>", lambda _e: self._on_assistant_send())

        self.assistant_send_btn = ttk.Button(
            entry_row,
            text="Send",
            command=self._on_assistant_send,
        )
        self.assistant_send_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.assistant_mic_btn = ttk.Button(
            entry_row,
            text="Mic",
            command=self._on_assistant_mic,
        )
        self.assistant_mic_btn.pack(side=tk.LEFT, padx=(8, 0))

        self._append_chat("Assistant", "Ask what you can cook with your pantry items.")

    def _append_chat(self, role: str, message: str) -> None:
        if not self.assistant_output:
            return
        self.assistant_output.configure(state="normal")
        self.assistant_output.insert(tk.END, f"{role}: {message}\n\n")
        self.assistant_output.see(tk.END)
        self.assistant_output.configure(state="disabled")

    def _on_assistant_send(self) -> None:
        if not self.assistant_entry or not self.assistant_send_btn:
            return
        text = self.assistant_entry.get().strip()
        if not text:
            return

        self.assistant_entry.delete(0, tk.END)
        self._append_chat("You", text)
        self.assistant_send_btn.configure(state="disabled")

        worker = threading.Thread(target=self._assistant_worker, args=(text,), daemon=True)
        worker.start()

    def _assistant_worker(self, user_text: str) -> None:
        reply = ask_pantry_assistant(user_text)
        self.after(0, lambda: self._finish_assistant_response(reply))

    def _finish_assistant_response(self, reply: str) -> None:
        self._append_chat("Assistant", reply)
        if self.assistant_send_btn:
            self.assistant_send_btn.configure(state="normal")

    def _on_assistant_mic(self) -> None:
        if self._mic_busy:
            return
        self._mic_request_id += 1
        request_id = self._mic_request_id
        if self.assistant_mic_btn:
            self.assistant_mic_btn.configure(state="disabled", text="Listening...")
        self._mic_busy = True
        self._append_chat("Assistant", "Listening for 5 seconds...")
        self.after(6000, lambda rid=request_id: self._maybe_set_transcribing(rid))
        self.after(90000, lambda rid=request_id: self._maybe_timeout_mic(rid))
        worker = threading.Thread(target=self._assistant_mic_worker, daemon=True)
        worker.start()

    def _assistant_mic_worker(self) -> None:
        request_id = self._mic_request_id
        try:
            transcript = record_and_transcribe(duration_seconds=5)
        except Exception as e:
            error_text = str(e)
            self.after(0, lambda rid=request_id, msg=error_text: self._finish_mic_error(rid, msg))
            return
        self.after(0, lambda rid=request_id, txt=transcript: self._finish_mic_success(rid, txt))

    def _maybe_set_transcribing(self, request_id: int) -> None:
        if not self._mic_busy or request_id != self._mic_request_id:
            return
        if self.assistant_mic_btn:
            self.assistant_mic_btn.configure(text="Transcribing...")

    def _maybe_timeout_mic(self, request_id: int) -> None:
        if not self._mic_busy or request_id != self._mic_request_id:
            return
        self._finish_mic_error(
            request_id,
            "Speech processing timed out. Try again. The first run may take longer while the model downloads.",
        )

    def _finish_mic_error(self, request_id: int, error_text: str) -> None:
        if request_id != self._mic_request_id:
            return
        self._mic_busy = False
        if self.assistant_mic_btn:
            self.assistant_mic_btn.configure(state="normal", text="Mic")
        messagebox.showerror("Speech to text error", error_text)

    def _finish_mic_success(self, request_id: int, transcript: str) -> None:
        if request_id != self._mic_request_id:
            return
        self._mic_busy = False
        if self.assistant_mic_btn:
            self.assistant_mic_btn.configure(state="normal", text="Mic")

        cleaned = (transcript or "").strip()
        if not cleaned:
            self._append_chat("Assistant", "I could not detect speech. Try again.")
            return

        if self.assistant_entry:
            self.assistant_entry.delete(0, tk.END)
            self.assistant_entry.insert(0, cleaned)
        self._on_assistant_send()

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
