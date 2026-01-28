"""pantry_app.py

Pantry feature module.

This file intentionally stays modular:
  - PantryPage: embeddable ttk.Frame you can mount inside a larger app shell.
  - PantryApp: standalone runner for the pantry module only.

The UI + behavior matches the previous single-file PantryApp (old app.py),
including barcode-scanner <Return> capture, categories, filtering, and details.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Callable, Optional

# from database import init_db_schema
from .pantry_model import (
    add_item,
    remove_item,
    get_all_items,
)
from .gui_windows import ItemDetailsWindow, CategoriesWindow, FilterWindow


class PantryPage(ttk.Frame):
    """Embeddable Pantry UI.

    Mount this frame inside any Tk root (e.g., the Home app shell). Call
    `activate()` when the page becomes visible so it captures scanner input.
    """

    STYLE_CONFIG: dict[str, str] = {}

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_home: Optional[Callable[[], None]] = None,
        padding: int = 0,  # keep the page tight to fit small screens
    ):
        super().__init__(master, padding=padding)
        self.on_home = on_home

        self.mode = "add"
        self.current_category_filter_id: Optional[int] = None

        self._setup_style()
        self._create_widgets()

        self.refresh_items()

    # --------- Styling (kept consistent with your existing modern palette) ---------

    def _setup_style(self) -> None:
        root = self.winfo_toplevel()
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Kitchen palette configuration
        self.STYLE_CONFIG.update(
            {
                "bg_main": "#f7f9fc",
                "bg_panel": "#ffffff",
                "accent_blue": "#4a90e2",
                "accent_blue_dark": "#357ab8",
                "accent_red": "#ff6b6b",
                "accent_red_dark": "#e05656",
                "text_main": "#1f2933",
                "text_muted": "#6b7b8c",
            }
        )

        root.configure(bg=self.STYLE_CONFIG["bg_main"])

        bg_main = self.STYLE_CONFIG["bg_main"]
        bg_panel = self.STYLE_CONFIG["bg_panel"]
        text_main = self.STYLE_CONFIG["text_main"]
        accent_blue = self.STYLE_CONFIG["accent_blue"]
        accent_red = self.STYLE_CONFIG["accent_red"]
        accent_blue_dark = self.STYLE_CONFIG["accent_blue_dark"]
        accent_red_dark = self.STYLE_CONFIG["accent_red_dark"]

        style.configure("TFrame", background=bg_main)
        style.configure("Card.TFrame", background=bg_panel, relief="flat", borderwidth=0)
        style.configure("TLabel", background=bg_main, foreground=text_main)

        style.configure(
            "Title.TLabel",
            font=("Segoe UI Semibold", 24),  # slightly smaller for small screens
            background=bg_main,
            foreground=text_main,
            padding=(0, 0, 0, 0),  # remove extra top/bottom padding
        )
        style.configure(
            "Mode.TLabel",
            font=("Segoe UI", 16),
            background=bg_main,
            foreground=accent_blue,
            padding=(8, 2),
        )
        style.configure(
            "Filter.TLabel",
            font=("Segoe UI", 12),
            background=bg_main,
            foreground=self.STYLE_CONFIG["text_muted"],
            padding=(2, 0),
        )

        # Treeview Styles
        style.configure(
            "Inventory.Treeview",
            background=bg_panel,
            fieldbackground=bg_panel,
            foreground=text_main,
            rowheight=32,  # slightly tighter so more rows fit
            bordercolor="#d0d7e2",
            borderwidth=1,
        )
        style.configure(
            "Inventory.Treeview.Heading",
            background="#e6f0fb",
            foreground=text_main,
            font=("Segoe UI Semibold", 13),
            relief="flat",
        )
        style.map(
            "Inventory.Treeview",
            background=[("selected", "#d8e8ff")],
            foreground=[("selected", text_main)],
        )

        # Big Button Styles (reduced padding so they don't overflow)
        style.configure(
            "AddBig.TButton",
            font=("Segoe UI Semibold", 16),
            padding=(14, 10),
            background=accent_blue,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
        )
        style.map("AddBig.TButton", background=[("active", accent_blue_dark)])

        style.configure(
            "RemoveBig.TButton",
            font=("Segoe UI Semibold", 16),
            padding=(14, 10),
            background=accent_red,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
        )
        style.map("RemoveBig.TButton", background=[("active", accent_red_dark)])

        style.configure("TopNav.TButton", font=("Segoe UI", 12), padding=(10, 6))

        # Detail/Danger Styles (for Toplevel windows)
        style.configure(
            "DetailTitle.TLabel",
            font=("Segoe UI Semibold", 20),
            background=bg_main,
            foreground=text_main,
            padding=(0, 0, 0, 8),
        )
        style.configure(
            "DetailSection.TLabel",
            font=("Segoe UI Semibold", 14),
            background=bg_main,
            foreground=self.STYLE_CONFIG["text_muted"],
            padding=(0, 10, 0, 2),
        )
        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 12),
            padding=(12, 8),
            background=accent_red,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
        )
        style.map("Danger.TButton", background=[("active", accent_red_dark)])

    # --------- UI ---------

    def _create_widgets(self) -> None:
        # Use grid so the center area expands and bottom stays visible on all screens
        self.grid_rowconfigure(2, weight=1)   # list/card expands
        self.grid_columnconfigure(0, weight=1)

        # --------- Top row: Title + Mode ----------
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 0))
        top_frame.grid_columnconfigure(1, weight=1)

        # Optional Home button (only shown when embedded in the home shell)
        col = 0
        if self.on_home is not None:
            back_btn = ttk.Button(
                top_frame,
                text="\u2190 Home",
                style="TopNav.TButton",
                command=self.on_home,
            )
            back_btn.grid(row=0, column=col, sticky="w", padx=(0, 10))
            col += 1

        title_label = ttk.Label(top_frame, text="Pantry Inventory", style="Title.TLabel")
        title_label.grid(row=0, column=col, sticky="w")
        col += 1

        self.mode_label = ttk.Label(top_frame, text="", style="Mode.TLabel")
        self.mode_label.grid(row=0, column=2, sticky="e")

        # --------- Second row: Categories + Filter ----------
        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 6))
        nav_frame.grid_columnconfigure(3, weight=1)

        self.categories_button = ttk.Button(
            nav_frame,
            text="Categories",
            style="TopNav.TButton",
            command=self.open_categories_window,
        )
        self.categories_button.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.filter_button = ttk.Button(
            nav_frame,
            text="Search & Filter",
            style="TopNav.TButton",
            command=self.open_filter_window,
        )
        self.filter_button.grid(row=0, column=1, sticky="w", padx=(0, 8))

        self.filter_label = ttk.Label(nav_frame, text="Filter: All locations", style="Filter.TLabel")
        self.filter_label.grid(row=0, column=2, sticky="w", padx=(6, 0))

        # --------- Center: Card with list ----------
        card_frame = ttk.Frame(self, style="Card.TFrame", padding=10)
        card_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 6))
        card_frame.grid_rowconfigure(0, weight=1)
        card_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            card_frame,
            columns=("name", "location", "age", "quantity"),
            show="headings",
            style="Inventory.Treeview",
            selectmode="browse",
        )
        self.tree.heading("name", text="Food", anchor="w")
        self.tree.heading("location", text="Location", anchor="center")
        self.tree.heading("age", text="Age", anchor="center")
        self.tree.heading("quantity", text="Qty", anchor="center")

        # Start with sane defaults; we will auto-resize these on window resize
        self.tree.column("name", anchor="w", width=420, stretch=True)
        self.tree.column("location", anchor="center", width=150, stretch=False)
        self.tree.column("age", anchor="center", width=90, stretch=False)
        self.tree.column("quantity", anchor="center", width=70, stretch=False)

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(card_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.on_item_activated)
        self.tree.bind("<Button-1>", self.on_tree_click, add="+")

        # Auto-size columns to prevent horizontal overflow on small screens
        self.winfo_toplevel().bind("<Configure>", self._on_root_configure, add="+")

        # --------- Bottom: Add / Remove big buttons ----------
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(4, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        self.add_button = ttk.Button(
            bottom_frame,
            text="Add Food",
            style="AddBig.TButton",
            command=self.switch_to_add_mode,
        )
        self.add_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.remove_button = ttk.Button(
            bottom_frame,
            text="Remove Food",
            style="RemoveBig.TButton",
            command=self.switch_to_remove_mode,
        )
        self.remove_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Hidden barcode entry for scanner
        self.barcode_entry = ttk.Entry(self)
        self.barcode_entry.place(x=-1000, y=-1000)

        # Start in add mode
        self.switch_to_add_mode()

        # Shortcuts for dev
        root = self.winfo_toplevel()
        root.bind("<F1>", lambda e: self.switch_to_add_mode())
        root.bind("<F2>", lambda e: self.switch_to_remove_mode())

    def _on_root_configure(self, event=None) -> None:
        """Resize tree columns based on available width so nothing spills off-screen."""
        # Card content width is root width minus our side padding.
        root = self.winfo_toplevel()
        total = max(320, root.winfo_width() - 24 - 24 - 22)  # approx margins/scrollbar
        qty_w = 70
        age_w = 90
        loc_w = 150

        # If screen is tight, shrink fixed cols a bit
        if total < 520:
            loc_w = 120
            age_w = 80
            qty_w = 60

        fixed = loc_w + age_w + qty_w
        name_w = max(180, total - fixed)

        try:
            self.tree.column("location", width=loc_w)
            self.tree.column("age", width=age_w)
            self.tree.column("quantity", width=qty_w)
            self.tree.column("name", width=name_w)
        except tk.TclError:
            # Tree might not be ready during early init
            return

    # --------- Page lifecycle ---------

    def activate(self) -> None:
        """Call when this page is shown to capture scanner input."""
        root = self.winfo_toplevel()
        root.bind("<Return>", self.on_barcode_scanned)
        self.focus_barcode_entry()

    def deactivate(self) -> None:
        """Call when this page is hidden."""
        root = self.winfo_toplevel()
        root.unbind("<Return>")

    # ---------- Time since scan formatting ----------

    def _format_age(self, last_scanned: Optional[str]) -> str:
        if not last_scanned:
            return "-"
        try:
            t = datetime.fromisoformat(last_scanned)
        except ValueError:
            return "-"

        delta = datetime.now() - t
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        if hours < 48:
            return f"{hours}h"
        days = hours // 24
        return f"{days}d"

    # ---------- List refresh ----------

    def refresh_items(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        items = get_all_items(category_id=self.current_category_filter_id)
        for barcode, name, display_location, last_scanned, qty in items:
            display_location = display_location if display_location else "-"
            age_text = self._format_age(last_scanned)
            self.tree.insert("", tk.END, iid=barcode, values=(name, display_location, age_text, qty))

    # ---------- Modes / scanning ----------

    def switch_to_add_mode(self) -> None:
        self.mode = "add"
        self.mode_label.config(text="Mode: ADDING", foreground=self.STYLE_CONFIG["accent_blue"])
        self.focus_barcode_entry()

    def switch_to_remove_mode(self) -> None:
        self.mode = "remove"
        self.mode_label.config(text="Mode: REMOVING", foreground=self.STYLE_CONFIG["accent_red"])
        self.focus_barcode_entry()

    def focus_barcode_entry(self) -> None:
        self.barcode_entry.delete(0, tk.END)
        self.after(50, self.barcode_entry.focus_set)

    def on_barcode_scanned(self, event=None) -> None:
        barcode = self.barcode_entry.get().strip()
        if not barcode:
            self.focus_barcode_entry()
            return

        if self.mode == "add":
            ok = add_item(barcode)
            if not ok:
                messagebox.showwarning("Unknown barcode", f"No product found for barcode: {barcode}")
        else:
            ok = remove_item(barcode)
            if not ok:
                messagebox.showinfo("Not found", f"Item with barcode {barcode} is not in the pantry.")

        self.refresh_items()
        self.focus_barcode_entry()

    # ---------- Tree click handling (location dropdown) ----------

    def on_tree_click(self, event) -> None:
        region = self.tree.identify("region", event.x, event.y)
        col = self.tree.identify_column(event.x)
        rowid = self.tree.identify_row(event.y)

        if region != "cell" or col != "#2" or not rowid:
            return

        self.tree.selection_set(rowid)
        self.tree.focus(rowid)

        values = self.tree.item(rowid, "values")
        current_location = values[1] if len(values) >= 2 else "-"
        barcode = rowid
        self.show_location_menu(barcode, current_location, event)

    def show_location_menu(self, barcode: str, current_location: str, event) -> None:
        cats = get_all_storage_categories()
        if not cats:
            messagebox.showinfo(
                "No categories",
                "You haven't created any locations yet.\n\nUse the 'Categories' button to add some first.",
            )
            return

        root = self.winfo_toplevel()
        menu = tk.Menu(root, tearoff=0)

        for cid, name in cats:
            label = f"\u2713 {name}" if current_location == name else name
            menu.add_command(label=label, command=lambda cid=cid: self._set_location(barcode, cid))

        menu.add_separator()
        menu.add_command(label="Clear location", command=lambda: self._set_location(barcode, None))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _set_location(self, barcode: str, category_id: Optional[int]) -> None:
        assign_item_to_category(barcode, category_id)
        self.refresh_items()
        self.tree.focus(barcode)
        self.tree.selection_set(barcode)

    # ---------- Toplevel window calls ----------

    def on_item_activated(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return
        barcode = selected
        ItemDetailsWindow(self.winfo_toplevel(), barcode, self.refresh_items, self.STYLE_CONFIG)

    def open_categories_window(self) -> None:
        CategoriesWindow(self.winfo_toplevel(), self.refresh_items, self.STYLE_CONFIG)

    def open_filter_window(self) -> None:
        FilterWindow(
            self.winfo_toplevel(),
            self.current_category_filter_id,
            self._update_filter,
            self.STYLE_CONFIG,
        )

    def _update_filter(self, new_filter_id, new_filter_name) -> None:
        self.current_category_filter_id = new_filter_id
        self.filter_label.config(text=f"Filter: {new_filter_name}")
        self.refresh_items()


class PantryApp(tk.Tk):
    """Standalone runner for just the pantry module."""

    def __init__(self):
        super().__init__()
        self.title("Pantry Manager")
        self.geometry("1024x600")
        self.option_add("*Font", ("Segoe UI", 14))

        page = PantryPage(self, on_home=None, padding=0)
        page.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        page.activate()


def main() -> None:
    app = PantryApp()
    app.mainloop()


if __name__ == "__main__":
    main()
