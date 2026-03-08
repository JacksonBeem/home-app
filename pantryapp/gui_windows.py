# gui_windows.py
import tkinter as tk
from tkinter import ttk, messagebox
# Import only available model functions
from .pantry_model import (
    delete_item,
    get_product_details,
    get_all_storage_categories,
    create_storage_category,
    delete_storage_category,
    add_manual_lookup_and_item,
)

# --- Toplevel Window Helper Classes ---

def _center_window(win):
    win.update_idletasks()
    width = win.winfo_width() or win.winfo_reqwidth()
    height = win.winfo_height() or win.winfo_reqheight()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = max(0, (screen_w // 2) - (width // 2))
    y = max(0, (screen_h // 2) - (height // 2))
    win.geometry(f"{width}x{height}+{x}+{y}")


def _build_scrollable_body(parent, bg_color):
    outer = ttk.Frame(parent)
    outer.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(outer, highlightthickness=0, bg=bg_color)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    content = ttk.Frame(canvas)
    win_id = canvas.create_window((0, 0), window=content, anchor="nw")

    def _on_content_configure(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        canvas.itemconfigure(win_id, width=event.width)

    def _on_mousewheel(event):
        if not canvas.winfo_exists():
            return "break"
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            return "break"
        return "break"

    def _unbind_mousewheel(_event=None):
        try:
            canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass

    content.bind("<Configure>", _on_content_configure)
    canvas.bind("<Configure>", _on_canvas_configure)
    canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", _unbind_mousewheel)
    canvas.bind("<Destroy>", _unbind_mousewheel)

    return content


class ItemDetailsWindow(tk.Toplevel):
    def __init__(self, master, barcode, refresh_callback, style_config):
        super().__init__(master)
        self.master = master
        self.barcode = barcode
        self.refresh_callback = refresh_callback
        self.style_config = style_config
        
        self.configure(bg=self.style_config["bg_main"])
        self.title("Product Details")
        self.geometry("400x560")
        self.transient(master)
        self.grab_set()

        try:
            self._load_and_create_widgets()
            _center_window(self)
        except Exception as e:
            messagebox.showerror(
                "Product details error",
                f"Could not display product details for barcode {self.barcode}.\n\n{e}",
            )
            self.destroy()

    def _load_and_create_widgets(self):
        # Attempt to fetch details from the master database
        product = get_product_details(self.barcode) 
        
        # Determine if metadata was found
        has_info = product is not None
        
        # Use fallback values if no product information is found
        name = self._as_text((product.get("name") if has_info else None), "Unknown product")
        brand = self._as_text((product.get("brand") if has_info else None), "")
        quantity = self._as_text((product.get("quantity") if has_info else None), "N/A")
        categories_str = self._as_text((product.get("categories") if has_info else None), "")
        description = self._as_text((product.get("description") if has_info else None), "N/A")

        # Format category string
        category_list = [c.strip() for c in categories_str.split(",") if c.strip()]
        if len(category_list) > 4:
            category_display = ", ".join(category_list[:4]) + "..."
        else:
            category_display = ", ".join(category_list) if category_list else "N/A"

        # Helper for nutrition formatting
        def fmt_val(key):
            if not has_info:
                return "N/A"
            val = product.get(key)
            if val is None:
                return "N/A"
            if isinstance(val, str):
                val = val.strip()
                if not val:
                    return "N/A"
            try:
                return f"{float(val):g}"
            except (TypeError, ValueError):
                return str(val)

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
        actions = ttk.Frame(self, padding=(20, 10, 20, 20))
        actions.pack(side=tk.BOTTOM, fill=tk.X)

        frame = _build_scrollable_body(self, self.style_config["bg_main"])
        frame.configure(padding=(20, 20, 20, 8))

        title = name if not brand else f"{brand} - {name}"
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
        self._create_info_section(frame, "Description:", description, pady_top=8, wraplength=380)

        ttk.Label(frame, text="Nutrition (per 100 g):",
                  style="DetailSection.TLabel").pack(anchor="w", pady=(12, 4))

        info_frame = ttk.Frame(frame)
        info_frame.pack(anchor="w", fill=tk.X)

        for label, value, unit in nutrition_data:
            self._create_nutrition_row(info_frame, label, value, unit)

        # Keep actions at the bottom so they remain visible even with long content.
        ttk.Button(
            actions,
            text="Delete from pantry",
            style="Danger.TButton",
            command=self._on_delete,
        ).pack(anchor="center", pady=(0, 6))

        ttk.Button(actions, text="Close", command=self.destroy).pack(anchor="center")

    def _create_info_section(self, parent, title, value, pady_top=0, wraplength=None):
        ttk.Label(parent, text=title, style="DetailSection.TLabel").pack(anchor="w", pady=(pady_top, 0))
        label = ttk.Label(parent, text=str(value), background=self.style_config["bg_main"], foreground=self.style_config["text_main"])
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

    def _as_text(self, value, default=""):
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default

    def _on_delete(self):
        if messagebox.askokcancel(
            "Delete item",
            "Remove this food from your pantry list?"
        ):
            delete_item(self.barcode) # Deletes from local pantry table
            self.refresh_callback()
            self.destroy()


class UnknownBarcodeDialog(tk.Toplevel):
    def __init__(self, master, barcode, style_config):
        super().__init__(master)
        self.barcode = barcode
        self.style_config = style_config
        self.result = False

        self.title("Item not found")
        self.geometry("430x230")
        self.resizable(False, False)
        self.configure(bg=self.style_config["bg_main"])
        self.transient(master)
        self.grab_set()

        self._create_widgets()
        _center_window(self)
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=(20, 20, 20, 16))
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Item not found",
            style="DetailTitle.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            frame,
            text=f"No product was found for barcode {self.barcode}.\nWould you like to add it?",
            background=self.style_config["bg_main"],
            foreground=self.style_config["text_main"],
            justify="left",
            wraplength=380,
        ).pack(anchor="w")

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(18, 0))

        ttk.Button(actions, text="Exit", command=self._on_exit).pack(side=tk.RIGHT)
        ttk.Button(actions, text="Add", command=self._on_add).pack(side=tk.RIGHT, padx=(0, 8))

    def _on_exit(self):
        self.result = False
        self.destroy()

    def _on_add(self):
        self.result = True
        self.destroy()


class AddItemWindow(tk.Toplevel):
    def __init__(self, master, barcode, refresh_callback, style_config):
        super().__init__(master)
        self.barcode = barcode
        self.refresh_callback = refresh_callback
        self.style_config = style_config
        self.fields = {}

        self.title("Add Product")
        self.geometry("520x600")
        self.configure(bg=self.style_config["bg_main"])
        self.transient(master)
        self.grab_set()

        self._create_widgets()
        _center_window(self)

    def _create_widgets(self):
        frame = _build_scrollable_body(self, self.style_config["bg_main"])
        frame.configure(padding=(20, 16, 20, 12))
        frame.columnconfigure(1, weight=1)

        ttk.Label(
            frame,
            text="Add New Product",
            style="DetailTitle.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ttk.Label(
            frame,
            text=f"Barcode: {self.barcode}",
            background=self.style_config["bg_main"],
            foreground=self.style_config["text_muted"],
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(
            frame,
            text="Leave optional fields blank to save them as null.",
            background=self.style_config["bg_main"],
            foreground=self.style_config["text_muted"],
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        rows = [
            ("name", "Item name *"),
            ("description", "Description"),
            ("brand", "Brand"),
            ("quantity", "Package / serving size"),
            ("categories", "Categories (comma separated)"),
            ("energy_kcal_100g", "Calories (kcal/100g)"),
            ("fat_100g", "Fat (g/100g)"),
            ("saturated_fat_100g", "Saturated fat (g/100g)"),
            ("carbs_100g", "Carbs (g/100g)"),
            ("sugars_100g", "Sugars (g/100g)"),
            ("proteins_100g", "Protein (g/100g)"),
            ("salt_100g", "Salt (g/100g)"),
        ]

        row_num = 3
        for key, label in rows:
            self._add_entry_row(frame, row_num, key, label)
            row_num += 1

        actions = ttk.Frame(frame)
        actions.grid(row=row_num, column=0, columnspan=2, sticky="e", pady=(14, 0))

        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(actions, text="Add to pantry", command=self._on_save).pack(side=tk.RIGHT, padx=(0, 8))

        self.fields["name"].focus_set()

    def _add_entry_row(self, parent, row_num, key, label):
        ttk.Label(
            parent,
            text=label,
            background=self.style_config["bg_main"],
            foreground=self.style_config["text_main"],
        ).grid(row=row_num, column=0, sticky="w", pady=4, padx=(0, 10))

        entry = ttk.Entry(parent)
        entry.grid(row=row_num, column=1, sticky="ew", pady=4)
        self.fields[key] = entry

    def _on_save(self):
        payload = {}

        for key in ("name", "description", "brand", "quantity", "categories"):
            payload[key] = self.fields[key].get().strip() or None

        numeric_fields = [
            ("energy_kcal_100g", "Calories"),
            ("fat_100g", "Fat"),
            ("saturated_fat_100g", "Saturated fat"),
            ("carbs_100g", "Carbs"),
            ("sugars_100g", "Sugars"),
            ("proteins_100g", "Protein"),
            ("salt_100g", "Salt"),
        ]
        for key, label in numeric_fields:
            raw = self.fields[key].get().strip()
            if not raw:
                payload[key] = None
                continue
            try:
                payload[key] = float(raw)
            except ValueError:
                messagebox.showwarning("Invalid value", f"{label} must be a number or blank.")
                return

        if not payload.get("name"):
            messagebox.showwarning("Missing name", "Item name is required.")
            return

        ok, error_message = add_manual_lookup_and_item(self.barcode, payload)
        if not ok:
            messagebox.showerror("Could not add item", error_message or "Unable to save item.")
            return

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
        _center_window(self)

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
        _center_window(self)

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


