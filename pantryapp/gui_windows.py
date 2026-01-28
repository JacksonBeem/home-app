# gui_windows.py
import tkinter as tk
from tkinter import ttk, messagebox
# Import only available model functions
from .pantry_model import delete_item

# --- Toplevel Window Helper Classes ---

class ItemDetailsWindow(tk.Toplevel):
    def __init__(self, master, barcode, refresh_callback, style_config):
        super().__init__(master)
        self.master = master
        self.barcode = barcode
        self.refresh_callback = refresh_callback
        self.style_config = style_config
        
        self.configure(bg=self.style_config["bg_main"])
        self.title("Product Details")
        self.geometry("420x640")
        self.transient(master)
        self.grab_set()

        self._load_and_create_widgets()

    def _load_and_create_widgets(self):
        # Attempt to fetch details from the master database
        product = get_product_details(self.barcode) 
        
        # Determine if metadata was found
        has_info = product is not None
        
        # Use fallback values if no product information is found
        name = (product.get("name") if has_info else None) or "Unknown product"
        brand = (product.get("brand") if has_info else None) or ""
        quantity = (product.get("quantity") if has_info else None) or "N/A"
        categories_str = (product.get("categories") if has_info else None) or ""

        # Format category string
        category_list = [c.strip() for c in categories_str.split(",") if c.strip()]
        if len(category_list) > 4:
            category_display = ", ".join(category_list[:4]) + "…"
        else:
            category_display = ", ".join(category_list) if category_list else "N/A"

        # Helper for nutrition formatting
        def fmt_val(key):
            if not has_info: return "N/A"
            val = product.get(key)
            return "N/A" if val is None else f"{val:g}"

        nutrition_data = [
            ("Energy", fmt_val("energy_kcal_100g"), "kcal"),
            ("Fat", fmt_val("fat_100g"), "g"),
            ("Saturated fat", fmt_val("saturated_fat_100g"), "g"),
            ("Carbohydrates", fmt_val("carbs_100g"), "g"),
            ("Sugars", fmt_val("sugars_100g"), "g"),
            ("Proteins", fmt_val("proteins_100g"), "g"),
            ("Salt", fmt_val("salt_100g"), "g"),
        ]

        # UI creation
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        title = name if not brand else f"{brand} – {name}"
        ttk.Label(frame, text=title, style="DetailTitle.TLabel",
                  wraplength=380, justify="left").pack(anchor="w")

        # Display a status message if info is missing
        if not has_info:
            ttk.Label(frame, text=f"Barcode: {self.barcode}", 
                      background=self.style_config["bg_main"], foreground="gray").pack(anchor="w")
            ttk.Label(frame, text="(Detailed info not found in database)", 
                      background=self.style_config["bg_main"], foreground="#ff6b6b", 
                      font=("Segoe UI", 10, "italic")).pack(anchor="w", pady=(0, 10))

        self._create_info_section(frame, "Package / serving size:", quantity)
        self._create_info_section(frame, "Categories:", category_display, pady_top=8, wraplength=380)

        ttk.Label(frame, text="Nutrition (per 100 g):",
                  style="DetailSection.TLabel").pack(anchor="w", pady=(12, 4))

        info_frame = ttk.Frame(frame)
        info_frame.pack(anchor="w", fill=tk.X)

        for label, value, unit in nutrition_data:
            self._create_nutrition_row(info_frame, label, value, unit)

        # Action Buttons - The Delete button is now always available
        ttk.Button(
            frame,
            text="Delete from pantry",
            style="Danger.TButton",
            command=self._on_delete,
        ).pack(anchor="center", pady=(24, 4))

        ttk.Button(frame, text="Close", command=self.destroy).pack(anchor="center", pady=(4, 0))

    def _create_info_section(self, parent, title, value, pady_top=0, wraplength=None):
        ttk.Label(parent, text=title, style="DetailSection.TLabel").pack(anchor="w", pady=(pady_top, 0))
        label = ttk.Label(parent, text=value, background=self.style_config["bg_main"], foreground=self.style_config["text_main"])
        if wraplength:
            label.config(wraplength=wraplength, justify="left")
        label.pack(anchor="w")

    def _create_nutrition_row(self, parent, label, value, unit=""):
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=2)
        ttk.Label(row_frame, text=label + ":", background=self.style_config["bg_main"],
                  foreground=self.style_config["text_main"]).pack(side=tk.LEFT)
        text = value if unit == "" or value == "N/A" else f"{value} {unit}"
        ttk.Label(row_frame, text=text, background=self.style_config["bg_main"],
                  foreground=self.style_config["text_main"]).pack(side=tk.RIGHT)

    def _on_delete(self):
        if messagebox.askokcancel(
            "Delete item",
            "Remove this food from your pantry list?"
        ):
            delete_item(self.barcode) # Deletes from local pantry table
            self.refresh_callback()
            self.destroy()


class CategoriesWindow(tk.Toplevel):
    def __init__(self, master, refresh_callback, style_config):
        super().__init__(master)
        self.master = master
        self.refresh_callback = refresh_callback
        self.style_config = style_config
        self._categories_cache = []

        self.title("Manage categories")
        self.geometry("480x400")
        self.configure(bg=self.style_config["bg_main"])
        self.transient(master)
        self.grab_set()

        self._create_widgets()
        self._refresh_category_listbox()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Storage locations (e.g., Fridge, Freezer, Basement):",
            background=self.style_config["bg_main"],
            foreground=self.style_config["text_main"]
        ).pack(anchor="w", pady=(0, 8))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.cat_listbox = tk.Listbox(
            list_frame,
            height=8,
            font=("Segoe UI", 13),
            selectmode=tk.SINGLE
        )
        self.cat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.cat_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cat_listbox.config(yscrollcommand=scrollbar.set)

        add_frame = ttk.Frame(frame)
        add_frame.pack(fill=tk.X, pady=(10, 4))
        ttk.Label(add_frame, text="Add new location:", background=self.style_config["bg_main"]).pack(anchor="w")

        entry_frame = ttk.Frame(add_frame)
        entry_frame.pack(fill=tk.X, pady=(4, 0))
        self.new_cat_var = tk.StringVar()
        new_cat_entry = ttk.Entry(entry_frame, textvariable=self.new_cat_var)
        new_cat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        new_cat_entry.bind("<Return>", lambda e: self._on_add_category())
        ttk.Button(entry_frame, text="Add", command=self._on_add_category).pack(side=tk.LEFT, padx=(8, 0))

        delete_frame = ttk.Frame(frame)
        delete_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(delete_frame, text="Delete selected", command=self._on_delete_cat).pack(side=tk.LEFT)
        ttk.Button(frame, text="Close", command=self.destroy).pack(anchor="e", pady=(16, 0))

    def _refresh_category_listbox(self):
        self.cat_listbox.delete(0, tk.END)
        self._categories_cache = get_all_storage_categories()
        for _id, name in self._categories_cache:
            self.cat_listbox.insert(tk.END, name)

    def _on_add_category(self):
        name = self.new_cat_var.get().strip()
        if name:
            ok, _ = create_storage_category(name)
            if not ok:
                messagebox.showinfo("Category exists", "That storage location already exists.")
            self.new_cat_var.set("")
            self._refresh_category_listbox()

    def _on_delete_cat(self):
        idx = self.cat_listbox.curselection()
        if idx:
            cat_id, name = self._categories_cache[idx[0]]
            if messagebox.askokcancel("Delete location", f"Delete '{name}'?"):
                delete_storage_category(cat_id)
                self._refresh_category_listbox()
                self.refresh_callback()


class FilterWindow(tk.Toplevel):
    def __init__(self, master, current_filter_id, update_filter_callback, style_config):
        super().__init__(master)
        self.master = master
        self.current_filter_id = current_filter_id
        self.update_filter_callback = update_filter_callback
        self.style_config = style_config
        self.cats = get_all_storage_categories()

        self.title("Search & filter")
        self.geometry("360x220")
        self.configure(bg=self.style_config["bg_main"])
        self.transient(master)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Filter foods by location:", background=self.style_config["bg_main"]).pack(anchor="w")

        cat_names = ["All locations"] + [name for (_id, name) in self.cats]
        curr_idx = 0
        if self.current_filter_id is not None:
            for i, (cid, _name) in enumerate(self.cats):
                if cid == self.current_filter_id:
                    curr_idx = i + 1
                    break

        cat_var = tk.StringVar(value=cat_names[curr_idx])
        ttk.Combobox(frame, textvariable=cat_var, values=cat_names, state="readonly").pack(fill=tk.X, pady=(6, 16))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Clear filter", command=lambda: self._apply_filter(cat_var.get(), True)).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Apply filter", command=lambda: self._apply_filter(cat_var.get())).pack(side=tk.RIGHT, padx=(0, 8))
        
    def _apply_filter(self, choice, clear=False):
        new_id, new_name = None, "All locations"
        if not clear and choice != "All locations":
            for cid, name in self.cats:
                if name == choice:
                    new_id, new_name = cid, name
                    break
        self.update_filter_callback(new_id, new_name)
        self.destroy()