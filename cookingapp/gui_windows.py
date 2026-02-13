# gui_windows.py
# GUI windows for CookingApp (Tkinter-based)



import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
from selenium import webdriver


class RecipeDetailsWindow(tk.Toplevel):
    def __init__(self, master, recipe=None):
        super().__init__(master)
        self.title("Recipe Details")
        self.geometry("800x600")
        name = recipe.recipe_name if recipe and hasattr(recipe, "recipe_name") else "(Unnamed Recipe)"
        instructions = recipe.instructions if recipe and hasattr(recipe, "instructions") else "No instructions available."
        prep_time = recipe.prep_time if recipe and hasattr(recipe, "prep_time") else "N/A"
        cook_time = recipe.cook_time if recipe and hasattr(recipe, "cook_time") else "N/A"
        # Only display integer values for prep_time and cook_time
        if prep_time != "N/A":
            try:
                prep_time = int(float(prep_time))
            except Exception:
                pass
        if cook_time != "N/A":
            try:
                cook_time = int(float(cook_time))
            except Exception:
                pass
        video_url = recipe.video_url if recipe and hasattr(recipe, "video_url") else None
        image = recipe.image if recipe and hasattr(recipe, "image") else None
        ttk.Label(self, text=f"Name: {name}", font=("Segoe UI", 16)).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.image_label = None
        self.photo = None
        if image:
            try:
                pil_image = Image.open(io.BytesIO(image))
                pil_image = pil_image.resize((200, 200))
                self.photo = ImageTk.PhotoImage(pil_image)
                self.image_label = ttk.Label(self, image=self.photo)
                self.image_label.grid(row=0, column=1, sticky="w", padx=10, pady=10)
            except Exception as e:
                ttk.Label(self, text=f"Image (Error loading image)", font=("Segoe UI", 12)).grid(row=0, column=1, sticky="w", padx=10, pady=10)
        else:
            ttk.Label(self, text=f"Image: None", font=("Segoe UI", 12)).grid(row=0, column=1, sticky="w", padx=10, pady=10)
        ttk.Label(self, text=f"Prep Time: {prep_time} Minutes", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(self, text=f"Cook Time: {cook_time} Minutes", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(self, text=f"Instructions: {instructions}", font=("Segoe UI", 12), wraplength=380).grid(row=3, column=0, sticky="w", padx=10, pady=10)
        # We can add more fields as needed. We should add the media player in a separate column
        if video_url:
                # Position Tkinter window on left half of screen
                self.update_idletasks()
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                left_width = int(screen_width / 2)
                self.geometry(f"{left_width}x{screen_height}+0+0")

                # Open YouTube video in browser on right using Selenium
                try:
                    driver = webdriver.Chrome()
                    driver.set_window_position(left_width, 0)
                    driver.set_window_size(left_width, screen_height)
                    # If video_url is a YouTube ID, build embed URL
                    if "youtube.com" not in video_url:
                        video_url = f"https://www.youtube.com/watch?v={video_url}"
                    driver.get(video_url)
                except Exception as e:
                    print(f"Error launching browser: {e}")

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
