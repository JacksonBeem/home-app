import tkinter as tk
from tkinter import ttk
import requests
import os
from dotenv import load_dotenv
from PIL import Image, ImageTk
from io import BytesIO
import threading


# ================= API =================

load_dotenv()

TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
LOC_URL = "https://api.kroger.com/v1/locations"
PROD_URL = "https://api.kroger.com/v1/products"

import base64

CLIENT_ID = os.getenv("KROGER_USERNAME")
CLIENT_SECRET = os.getenv("KROGER_AUTH")

def bearer_token():
    creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(creds.encode()).decode()

    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "scope": "product.compact",
        },
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    #print("STATUS:", r.status_code)
    #print("RESPONSE:", r.text)

    return r.json()["access_token"]
def get_store(zipcode):
    r = requests.get(
        LOC_URL,
        params={"filter.zipCode.near": zipcode, "filter.limit": 1},
        headers={"Authorization": f"Bearer {bearer_token()}"},
    )
    return r.json()["data"][0]["locationId"]


# ================= PRODUCT PARSER =================

def _extract_number(val):
    """Safely coerce a value to float, return None if not possible."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def search_products(query, location):
    r = requests.get(
        PROD_URL,
        params={
            "filter.term": query,
            "filter.locationId": location,
            "filter.limit": 30,
            "filter.fulfillment": "ais",
        },
        headers={"Authorization": f"Bearer {bearer_token()}"},
    )
    data = r.json()
    products = []

    for p in data.get("data", []):
        name  = p.get("description", "")
        brand = p.get("brand", "")
        size  = ""
        regular = None
        promo   = None

        items = p.get("items", [])

        for item in items:
            if not size:
                size = item.get("size", "")

            # Check every known price container key
            for price_key in ("price", "storePrices", "nationalPrice", "prices"):
                price_data = item.get(price_key)
                if not price_data:
                    continue

                blobs = price_data if isinstance(price_data, list) else [price_data]

                for blob in blobs:
                    if not isinstance(blob, dict):
                        continue

                    for rkey in ("regular", "regularPrice", "listPrice",
                                 "originalPrice", "basePrice", "standardPrice"):
                        val = _extract_number(blob.get(rkey))
                        if val and (regular is None or val < regular):
                            regular = val

                    for pkey in ("promo", "sale", "discount", "salePrice",
                                 "promoPrice", "specialPrice", "dealPrice"):
                        val = _extract_number(blob.get(pkey))
                        if val and (promo is None or val < promo):
                            promo = val

        # Debug: show raw data for any product still missing a price
        if regular is None and promo is None:
            print(f"\n[NO PRICE] {name!r}")
            for i, item in enumerate(items):
                print(f"  item[{i}] keys: {list(item.keys())}")
                for k in ("price", "storePrices", "nationalPrice", "prices"):
                    if item.get(k):
                        print(f"    {k}: {item[k]}")

        price_value = promo if promo else regular
        price_str   = f"${price_value:.2f}" if price_value is not None else "N/A"

        # IMAGE — prefer medium, fall back to any size
        image_url = ""
        for img in p.get("images", []):
            if img.get("featured"):
                sizes  = img.get("sizes", [])
                chosen = {s.get("size"): s.get("url", "") for s in sizes}
                for sz in ("medium", "small", "thumbnail", "xlarge", "large"):
                    if chosen.get(sz):
                        image_url = chosen[sz]
                        break
                if not image_url and sizes:
                    image_url = sizes[0].get("url", "")

        products.append({
            "name":    name,
            "brand":   brand,
            "size":    size,
            "price":   price_str,
            "regular": regular,
            "promo":   promo,
            "image":   image_url,
        })

    return products


# ================= PALETTE — pantry app colours =================

BG_MAIN   = "#f7f9fc"   # pantry bg_main
SURFACE   = "#ffffff"   # pantry bg_panel
CARD_BG   = "#ffffff"   # white cards
ACCENT    = "#4a90e2"   # pantry accent_blue
ACCENT2   = "#357ab8"   # pantry accent_blue_dark
ACCENT_R  = "#ff6b6b"   # pantry accent_red
TEXT      = "#1f2933"   # pantry text_main
SUBTEXT   = "#6b7b8c"   # pantry text_muted
BORDER    = "#d0d7e2"   # pantry border
SALE_CLR  = "#27ae60"   # green for sale price
SALE_BG   = "#eafaf1"

FONT_HEAD = ("Segoe UI", 9, "bold")
FONT_SUB  = ("Segoe UI", 8)
FONT_PRC  = ("Segoe UI", 11, "bold")
FONT_UI   = ("Segoe UI", 10)
FONT_BTN  = ("Segoe UI", 9, "bold")


class StoreApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Kroger Search")
        self.configure(bg=BG_MAIN)
        self.geometry("1200x720")
        self.minsize(900, 600)

        self.images        = []
        self.last_products = []
        self._active_filter = None

        self.create_ui()
        self.bind("<Configure>", self._on_resize)

    # ── UI ────────────────────────────────────────────────────────────────

    def create_ui(self):
        # Header bar
        header = tk.Frame(self, bg=BG_MAIN, pady=18)
        header.pack(fill="x", padx=28)

        tk.Label(
            header, text="🛒  Kroger Search",
            font=("Segoe UI", 18, "bold"),
            bg=BG_MAIN, fg=TEXT,
        ).pack(side="left")

        # Search row
        search_row = tk.Frame(self, bg=BG_MAIN)
        search_row.pack(fill="x", padx=28, pady=(0, 14))

        self.search_entry = self._entry(search_row, width=38, placeholder="Search products…")
        self.search_entry.pack(side="left", ipady=7, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        self.zip_entry = self._entry(search_row, width=9, placeholder="ZIP")
        self.zip_entry.pack(side="left", ipady=7, padx=(0, 12))
        self.zip_entry.bind("<Return>", lambda e: self._do_search())

        self._search_btn = self._btn(search_row, "Search", self._do_search, accent=True)
        self._search_btn.pack(side="left", ipady=6, ipadx=14)

        # Filter row
        filter_row = tk.Frame(self, bg=BG_MAIN)
        filter_row.pack(fill="x", padx=28, pady=(0, 8))

        self._filter_btns = {}
        for label, cmd_name in [
            ("Store Brand", "filter_store_brand"),
            ("Name Brand",  "filter_name_brand"),
            ("Cheapest",    "sort_cheapest"),
            ("On Sale",     "filter_sale"),
        ]:
            cmd = getattr(self, cmd_name)
            b = self._btn(filter_row, label, lambda c=cmd, l=label: self._apply_filter(c, l))
            b.pack(side="left", ipady=5, ipadx=10, padx=(0, 8))
            self._filter_btns[label] = b

        clear_b = self._btn(filter_row, "Clear", self._clear_filter)
        clear_b.pack(side="left", ipady=5, ipadx=10)
        self._filter_btns["Clear"] = clear_b

        # Divider
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(8, 0))

        # Status bar
        self.status_var = tk.StringVar(value="Enter a search term to get started.")
        tk.Label(
            self, textvariable=self.status_var,
            bg=BG_MAIN, fg=SUBTEXT, font=FONT_SUB, anchor="w"
        ).pack(fill="x", padx=28, pady=(6, 6))

        # Scrollable grid
        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        canvas = tk.Canvas(outer, bg=BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(canvas, bg=BG_MAIN)
        self._canvas_window = canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            self._canvas_window, width=e.width
        ))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._canvas = canvas

    # ── Widgets ───────────────────────────────────────────────────────────

    def _entry(self, parent, width=20, placeholder=""):
        e = tk.Entry(
            parent,
            font=FONT_UI,
            width=width,
            bg=SURFACE,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        if placeholder:
            e.insert(0, placeholder)
            e.config(fg=SUBTEXT)
            def on_focus_in(ev, ph=placeholder, widget=e):
                if widget.get() == ph:
                    widget.delete(0, "end")
                    widget.config(fg=TEXT)
            def on_focus_out(ev, ph=placeholder, widget=e):
                if not widget.get():
                    widget.insert(0, ph)
                    widget.config(fg=SUBTEXT)
            e.bind("<FocusIn>",  on_focus_in)
            e.bind("<FocusOut>", on_focus_out)
        return e

    def _btn(self, parent, text, cmd, accent=False):
        bg = ACCENT  if accent else SURFACE
        fg = "#ffffff" if accent else SUBTEXT
        b = tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=bg,
            fg=fg,
            font=FONT_BTN,
            relief="flat",
            cursor="hand2",
            activebackground=ACCENT2 if accent else "#e6f0fb",
            activeforeground="#ffffff" if accent else TEXT,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        b.bind("<Enter>", lambda e: b.config(bg=ACCENT2 if accent else "#e6f0fb",
                                              fg="#ffffff" if accent else TEXT))
        b.bind("<Leave>", lambda e: b.config(bg=ACCENT  if accent else SURFACE,
                                              fg="#ffffff" if accent else SUBTEXT))
        return b

    # ── Search ────────────────────────────────────────────────────────────

    def _get_text(self, entry, placeholder):
        val = entry.get()
        return "" if val == placeholder else val

    def _do_search(self):
        query = self._get_text(self.search_entry, "Search products…")
        zipc  = self._get_text(self.zip_entry, "ZIP")
        if not query or not zipc:
            self.status_var.set("Please enter both a search term and a ZIP code.")
            return
        self._search_btn.config(state="disabled", text="Searching…")
        self.status_var.set("Fetching results…")
        threading.Thread(target=self._fetch, args=(query, zipc), daemon=True).start()

    def _fetch(self, query, zipc):
        try:
            loc      = get_store(zipc)
            products = search_products(query, loc)
            self.after(0, self._on_results, products)
        except Exception as ex:
            self.after(0, lambda: self.status_var.set(f"Error: {ex}"))
            self.after(0, lambda: self._search_btn.config(state="normal", text="Search"))

    def _on_results(self, products):
        self.last_products  = products
        self._active_filter = None
        self._search_btn.config(state="normal", text="Search")
        count = len(products)
        self.status_var.set(f"{count} result{'s' if count != 1 else ''} found.")
        self.show_products(products)

    # ── Filters ───────────────────────────────────────────────────────────

    def _apply_filter(self, fn, label):
        self._active_filter = label
        fn()

    def _clear_filter(self):
        self._active_filter = None
        self.show_products(self.last_products)
        self.status_var.set(f"{len(self.last_products)} result(s) — filter cleared.")

    def filter_store_brand(self):
        r = [p for p in self.last_products if "kroger" in p["brand"].lower()]
        self.status_var.set(f"{len(r)} store-brand result(s).")
        self.show_products(r)

    def filter_name_brand(self):
        r = [p for p in self.last_products if "kroger" not in p["brand"].lower()]
        self.status_var.set(f"{len(r)} name-brand result(s).")
        self.show_products(r)

    def sort_cheapest(self):
        r = sorted(
            self.last_products,
            key=lambda p: float(p["price"].replace("$", "")) if p["price"] != "N/A" else 9999,
        )
        self.status_var.set("Sorted by price (lowest first).")
        self.show_products(r)

    def filter_sale(self):
        r = [p for p in self.last_products if p["promo"]]
        self.status_var.set(f"{len(r)} on-sale item(s).")
        self.show_products(r)

    # ── Grid ──────────────────────────────────────────────────────────────

    def _on_resize(self, event):
        pass

    def show_products(self, products):
        self.images.clear()
        for w in self.grid_frame.winfo_children():
            w.destroy()

        cols = 5
        for i, p in enumerate(products):
            self.create_card(p, i // cols, i % cols)

    # ── Image ─────────────────────────────────────────────────────────────

    def load_image(self, url):
        if not url:
            return None
        try:
            r   = requests.get(url, timeout=5)
            img = Image.open(BytesIO(r.content)).convert("RGBA")
            img.thumbnail((110, 110), Image.LANCZOS)
            tkimg = ImageTk.PhotoImage(img)
            self.images.append(tkimg)
            return tkimg
        except Exception:
            return None

    # ── Card ──────────────────────────────────────────────────────────────

    def create_card(self, p, row, col):
        card = tk.Frame(
            self.grid_frame,
            bg=CARD_BG,
            width=190,
            height=260,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        # Image area — soft grey tint like pantry panel inset
        img_frame = tk.Frame(card, bg="#f0f4f8", height=120)
        img_frame.pack(fill="x")
        img_frame.pack_propagate(False)

        img = self.load_image(p["image"])
        if img:
            tk.Label(img_frame, image=img, bg="#f0f4f8").pack(expand=True)
        else:
            tk.Label(img_frame, text="🛒", font=("Segoe UI", 28),
                     bg="#f0f4f8", fg=SUBTEXT).pack(expand=True)

        # Sale badge
        if p["promo"]:
            tk.Label(
                card, text=" SALE ",
                bg=ACCENT_R, fg="white",
                font=("Segoe UI", 7, "bold"),
            ).place(x=6, y=6)

        # Divider
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x")

        # Info
        info = tk.Frame(card, bg=CARD_BG, padx=10)
        info.pack(fill="both", expand=True, pady=(8, 6))

        tk.Label(
            info, text=p["name"],
            wraplength=160, justify="left",
            bg=CARD_BG, fg=TEXT,
            font=FONT_HEAD, anchor="w",
        ).pack(fill="x")

        meta = f'{p["brand"]}{"  •  " + p["size"] if p["size"] else ""}'
        tk.Label(
            info, text=meta,
            wraplength=160, justify="left",
            bg=CARD_BG, fg=SUBTEXT,
            font=FONT_SUB, anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Price row
        price_frame = tk.Frame(info, bg=CARD_BG)
        price_frame.pack(fill="x", pady=(6, 0))

        price_color = SALE_CLR if p["promo"] else TEXT
        if p["price"] == "N/A":
            price_color = ACCENT_R

        tk.Label(
            price_frame,
            text=p["price"],
            fg=price_color,
            bg=CARD_BG,
            font=FONT_PRC,
        ).pack(side="left")

        if p["promo"] and p["regular"]:
            tk.Label(
                price_frame,
                text=f'  ${p["regular"]:.2f}',
                fg=SUBTEXT,
                bg=CARD_BG,
                font=("Segoe UI", 9),
            ).pack(side="left")


# ================= RUN =================

if __name__ == "__main__":
    app = StoreApp()
    app.mainloop()