# cooking_app.py
# Main entry point for CookingApp


import tkinter as tk
from tkinter import ttk, messagebox
from cookingapp.cooking_model import RecipeManager
from cookingapp.gui_windows import RecipeDetailsWindow, RecipeListWindow
# Embeddable CookingPage for HomeApp
global FAVORITE_RECIPES
class CookingPage(ttk.Frame):
    """Embeddable Cooking UI (like PantryPage)."""
    def __init__(self, master, *, on_home=None, padding=0):
        super().__init__(master, padding=padding)
        self.on_home = on_home
        self.manager = RecipeManager()
        self._setup_style()
        self._create_widgets()

    def _setup_style(self):
        style = ttk.Style(self.winfo_toplevel())
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 24))
        style.configure("Mode.TLabel", font=("Segoe UI", 16), foreground="#4a90e2", padding=(8, 2))
        style.configure("Filter.TLabel", font=("Segoe UI", 12), foreground="#6b7b8c", padding=(2, 0))
        style.configure("TopNav.TButton", font=("Segoe UI", 12), padding=(10, 6))

    def _create_widgets(self):
        # Top row: Home button, Title, Mode
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(6, 0))
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
        title_label = ttk.Label(top_frame, text="Cooking", style="Title.TLabel")
        title_label.grid(row=0, column=col, sticky="w")
        col += 1
        self.mode_label = ttk.Label(top_frame, text="", style="Mode.TLabel")
        self.mode_label.grid(row=0, column=2, sticky="e")

        # Second row: Person filter, Add/View buttons
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(4, 6))
        nav_frame.grid_columnconfigure(4, weight=1)

        # Person dropdown
        from models.person import Person
        from sqlalchemy.orm import sessionmaker
        from database import engine
        Session = sessionmaker(bind=engine)
        session = Session()

        def get_selected_person():
            global FAVORITE_RECIPES
            selected_name = self.person_var.get()
            selected_person = next((p for p in people if f"{p.first_name} {p.last_name}" == selected_name), None)
            if selected_person:
                person_id = selected_person.person_id
            FAVORITE_RECIPES = self.manager.get_favorite_recipes(person_id)
            self.refresh_recipes(FAVORITE_RECIPES)

        people = self.manager.get_all_people()
        self.person_var = tk.StringVar()
        person_names = [f"{p.first_name} {p.last_name}" for p in people]
        self.person_dropdown = ttk.Combobox(nav_frame, textvariable=self.person_var, values=person_names, state="readonly", width=18)
        self.person_dropdown.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.person_dropdown.set(person_names[0] if person_names else "")

        ttk.Button(nav_frame, text="Show All Recipes", style="TopNav.TButton", command=lambda: self.refresh_recipes()).grid(row=0, column=1, sticky="w", padx=(0, 8))
        ttk.Button(nav_frame, text="Show Favorites", style="TopNav.TButton", command=lambda: get_selected_person()).grid(row=0, column=2, sticky="w", padx=(0, 8))

        # Add/View buttons
        ttk.Button(nav_frame, text="Add Recipe", style="TopNav.TButton", command=self._add_recipe).grid(row=0, column=3, sticky="w", padx=(0, 8))
        #ttk.Button(nav_frame, text="View Favorite Recipes", style="TopNav.TButton", command=self._open_recipe_list).grid(row=0, column=3, sticky="w", padx=(0, 8))

        # Spacer
        if self.on_home:
            ttk.Button(nav_frame, text="Home", style="TopNav.TButton", command=self.on_home).grid(row=0, column=4, sticky="e", padx=(0, 4))

        # Recipe list
        self.recipe_listbox = tk.Listbox(self, height=10)
        self.recipe_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.recipe_listbox.bind("<Double-Button-1>", self._on_recipe_open)
        self.refresh_recipes()

    def refresh_recipes(self, favorite_recipes=None):
        if favorite_recipes is not None:
            self.recipe_listbox.delete(0, tk.END)
            for recipe in favorite_recipes:
                self.recipe_listbox.insert(tk.END, getattr(recipe, "recipe_name", "(Unnamed Recipe)"))
        else:
            self.recipe_listbox.delete(0, tk.END)
            for recipe in self.manager.get_all_recipes():
                self.recipe_listbox.insert(tk.END, getattr(recipe, "recipe_name", "(Unnamed Recipe)"))

    def _add_recipe(self):
        # For demo, just add a dummy recipe
        new_recipe = {"name": f"Recipe {len(self.manager.get_all_recipes())+1}"}
        self.manager.add_recipe(new_recipe)
        self.refresh_recipes()

    def _open_recipe_list(self):
        RecipeListWindow(self)

    def _on_recipe_open(self, event):
        idx = self.recipe_listbox.curselection()
        if not idx:
            return
        recipe = self.manager.get_all_recipes()[idx[0]]
        RecipeDetailsWindow(self, recipe=recipe)


# Standalone runner for CookingApp
class CookingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cooking Manager")
        self.geometry("900x600")
        self.option_add("*Font", ("Segoe UI", 14))
        page = CookingPage(self)
        page.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def main():
    app = CookingApp()
    app.mainloop()

if __name__ == "__main__":
    main()
