import tkinter as tk
from tkinter import ttk
import requests
import os
from dotenv import load_dotenv
from PIL import Image, ImageTk
from io import BytesIO

import database
from store import Store, create_tables

from sqlalchemy.orm import sessionmaker


SessionLocal = sessionmaker(bind=database.engine)


# ================= SAVE / COMPARE =================

def save_product(name, brand, price, location):

    session = SessionLocal()

    item = session.query(Store).filter_by(
        item_name=name,
        store_location=location
    ).first()

    if item:

        old_price = float(item.new_price)

        item.old_price = old_price
        item.new_price = price
        item.price_change = price - old_price

    else:

        item = Store(
            item_name=name,
            brand=brand,
            store_location=location,
            old_price=price,
            new_price=price,
            price_change=0,
        )

        session.add(item)

    session.commit()

    return float(item.price_change)


# ================= API =================

load_dotenv()

TOKEN_URL = "https://api-ce.kroger.com/v1/connect/oauth2/token"
LOC_URL = "https://api-ce.kroger.com/v1/locations"
PROD_URL = "https://api-ce.kroger.com/v1/products"

SECRET = os.getenv("KROGER_AUTH")


def bearer_token():

    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "scope": "product.compact",
        },
        headers={
            "Authorization": f"Basic {SECRET}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    return r.json()["access_token"]


def get_store(zipcode):

    r = requests.get(
        LOC_URL,
        params={
            "filter.zipCode.near": zipcode,
            "filter.limit": 1,
        },
        headers={
            "Authorization": f"Bearer {bearer_token()}",
        },
    )

    return r.json()["data"][0]["locationId"]


def search_products(query, location):

    r = requests.get(
        PROD_URL,
        params={
            "filter.term": query,
            "filter.locationId": location,
            "filter.limit": 12,
        },
        headers={
            "Authorization": f"Bearer {bearer_token()}",
        },
    )

    data = r.json()

    products = []

    for p in data["data"]:

        name = p.get("description", "")
        brand = p.get("brand", "")

        size = (
            p.get("items", [{}])[0]
            .get("size", "")
        )

        price_data = (
            p.get("items", [{}])[0]
            .get("price", {})
        )

        price = (
            price_data.get("promo")
            or price_data.get("sale")
            or price_data.get("regular")
            or None
        )

        price_str = "N/A"
        price_num = 0

        if price:
            price_str = f"${price}"
            price_num = float(price)

        image_url = ""

        for img in p.get("images", []):
            if img.get("featured"):
                for s in img.get("sizes", []):
                    if s.get("size") == "medium":
                        image_url = s.get("url")

        change = save_product(
            name,
            brand,
            price_num,
            location,
        )

        products.append(
            {
                "name": name,
                "brand": brand,
                "size": size,
                "price": price_str,
                "image": image_url,
                "change": change,
            }
        )

    return products


# ================= UI =================


class StoreApp(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("Store Search")
        self.geometry("1200x600")

        self.images = []

        self.last_products = []

        self.create_ui()

    # ---------- UI ----------

    def create_ui(self):

        top = ttk.Frame(self)
        top.pack(fill="x")

        self.search_entry = ttk.Entry(top)
        self.search_entry.pack(side="left", expand=True, fill="x")

        self.zip_entry = ttk.Entry(top, width=10)
        self.zip_entry.pack(side="left")

        ttk.Button(
            top,
            text="Search",
            command=self.on_search
        ).pack(side="left")

        ttk.Button(
            top,
            text="Store Brand",
            command=self.filter_store_brand
        ).pack(side="left")

        ttk.Button(
            top,
            text="Name Brand",
            command=self.filter_name_brand
        ).pack(side="left")

        ttk.Button(
            top,
            text="Cheapest",
            command=self.sort_cheapest
        ).pack(side="left")

        ttk.Button(
            top,
            text="On Sale",
            command=self.sort_sale
        ).pack(side="left")

        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack()

    # ---------- SEARCH ----------

    def on_search(self):

        query = self.search_entry.get()
        zipc = self.zip_entry.get()

        loc = get_store(zipc)

        self.last_products = search_products(query, loc)

        self.show_products(self.last_products)

    # ---------- FILTERS ----------

    def filter_store_brand(self):

        result = [
            p for p in self.last_products
            if "kroger" in p["brand"].lower()
        ]

        self.show_products(result)


    def filter_name_brand(self):

        result = [
            p for p in self.last_products
            if "kroger" not in p["brand"].lower()
        ]

        self.show_products(result)


    def sort_cheapest(self):

        result = sorted(
            self.last_products,
            key=lambda p: float(p["price"].replace("$", ""))
            if p["price"] != "N/A" else 999,
        )

        self.show_products(result)


    def sort_sale(self):

        result = [
            p for p in self.last_products
            if p["change"] < 0
        ]

        self.show_products(result)


    # ---------- SHOW ----------

    def show_products(self, products):

        self.images.clear()

        for w in self.grid_frame.winfo_children():
            w.destroy()

        for i, p in enumerate(products):

            r = i // 6
            c = i % 6

            self.create_card(p, r, c)


    # ---------- IMAGE ----------

    def load_image(self, url):

        try:

            r = requests.get(url)

            img = Image.open(BytesIO(r.content))

            img.thumbnail((100, 100))

            tkimg = ImageTk.PhotoImage(img)

            self.images.append(tkimg)

            return tkimg

        except:
            return None


    # ---------- CARD ----------

    def create_card(self, p, row, col):

        card = tk.Frame(
            self.grid_frame,
            width=160,
            height=230,
            bg="white",
        )

        card.grid(row=row, column=col, padx=10, pady=10)

        card.grid_propagate(False)

        img = self.load_image(p["image"])

        if img:
            tk.Label(card, image=img, bg="white").pack()

        tk.Label(
            card,
            text=p["name"],
            wraplength=140,
            bg="white"
        ).pack()

        tk.Label(
            card,
            text=f'{p["brand"]} • {p["size"]}',
            bg="white"
        ).pack()

        color = "black"

        if p["change"] < 0:
            color = "green"
        elif p["change"] > 0:
            color = "red"

        tk.Label(
            card,
            text=p["price"],
            fg=color,
            bg="white",
            font=("Arial", 11, "bold")
        ).pack()


# ================= RUN =================

if __name__ == "__main__":

    create_tables()

    app = StoreApp()
    app.mainloop()