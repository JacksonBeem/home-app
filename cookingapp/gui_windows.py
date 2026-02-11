# gui_windows.py
# GUI windows for CookingApp (Tkinter-based)

import tkinter as tk
from tkinter import ttk


class RecipeDetailsWindow(tk.Toplevel):
    def __init__(self, master, recipe=None):
        super().__init__(master)
        self.title("Recipe Details")
        self.geometry("400x300")
        name = getattr(recipe, "recipe_name", "(Unnamed Recipe)") if recipe else "(No Recipe)"
        ttk.Label(self, text=f"Name: {name}", font=("Segoe UI", 16)).pack(padx=10, pady=10)
        # Add more fields as needed



class RecipeListWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("All Recipes")
        self.geometry("400x400")
        ttk.Label(self, text="Recipe List", font=("Segoe UI", 16)).pack(padx=10, pady=10)
        listbox = tk.Listbox(self)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Try to get recipes from parent CookingPage if possible
        recipes = []
        parent = master
        if hasattr(parent, 'manager'):
            recipes = parent.manager.get_all_recipes()
        for recipe in recipes:
            listbox.insert(tk.END, getattr(recipe, "recipe_name", "(Unnamed Recipe)"))

    def _filter_favorites(self):
        # Filter recipes by is_favorite for selected person needs to be implemented in the model/database first
        selected_person = self.person_var.get()
        if not selected_person:
            messagebox.showinfo("No Person Selected", "Please select a person to filter favorites.")
            return
        filtered = [r for r in recipes if getattr(r, 'recipe_id', None) in fav_recipe_ids]
        self.recipe_listbox.delete(0, tk.END)
        for recipe in filtered:
            self.recipe_listbox.insert(tk.END, getattr(recipe, "recipe_name", "(Unnamed Recipe)"))

# Add more windows as needed
