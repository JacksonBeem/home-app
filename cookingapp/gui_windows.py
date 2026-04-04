# gui_windows.py
# GUI windows for CookingApp (Tkinter-based)



import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
from selenium import webdriver


class RecipeDetailsWindow(tk.Toplevel):
    def __init__(self, master, recipe=None):
        from ui_style import STYLE_CONFIG
        super().__init__(master)
        self.title("Recipe Details")
        self.geometry("700x480")
        self.configure(bg=STYLE_CONFIG["bg_main"])

        name = recipe.recipe_name if recipe and hasattr(recipe, "recipe_name") else "(Unnamed Recipe)"
        instructions = recipe.instructions if recipe and hasattr(recipe, "instructions") else "No instructions available."
        prep_time = recipe.prep_time if recipe and hasattr(recipe, "prep_time") else "N/A"
        cook_time = recipe.cook_time if recipe and hasattr(recipe, "cook_time") else "N/A"
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

        # Card-like frame for content
        card = tk.Frame(self, bg=STYLE_CONFIG["bg_panel"], bd=0, highlightthickness=1, highlightbackground=STYLE_CONFIG["card_shadow"])
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.92)

        # Title
        title = ttk.Label(card, text=name, font=(STYLE_CONFIG["font_bold"], 22), background=STYLE_CONFIG["bg_panel"], foreground=STYLE_CONFIG["text_main"])
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=(24, 8), pady=(18, 8))

        # Image and details side by side
        img_frame = tk.Frame(card, bg=STYLE_CONFIG["bg_panel"])
        img_frame.grid(row=1, column=0, rowspan=3, sticky="nw", padx=(24, 8), pady=(0, 8))
        self.photo = None
        if image:
            try:
                pil_image = Image.open(io.BytesIO(image))
                pil_image = pil_image.resize((180, 180))
                self.photo = ImageTk.PhotoImage(pil_image)
                img_label = ttk.Label(img_frame, image=self.photo, background=STYLE_CONFIG["bg_panel"])
                img_label.pack()
            except Exception:
                ttk.Label(img_frame, text="Image (Error loading image)", font=(STYLE_CONFIG["font"], 12), background=STYLE_CONFIG["bg_panel"], foreground=STYLE_CONFIG["text_muted"]).pack()
        else:
            ttk.Label(img_frame, text="No Image", font=(STYLE_CONFIG["font"], 12), background=STYLE_CONFIG["bg_panel"], foreground=STYLE_CONFIG["text_muted"]).pack()

        # Details
        details_frame = tk.Frame(card, bg=STYLE_CONFIG["bg_panel"])
        details_frame.grid(row=1, column=1, sticky="nw", padx=(8, 24), pady=(0, 8))
        ttk.Label(details_frame, text=f"Prep Time: {prep_time} min", font=(STYLE_CONFIG["font"], 13), background=STYLE_CONFIG["bg_panel"], foreground=STYLE_CONFIG["text_main"]).pack(anchor="w", pady=(0, 4))
        ttk.Label(details_frame, text=f"Cook Time: {cook_time} min", font=(STYLE_CONFIG["font"], 13), background=STYLE_CONFIG["bg_panel"], foreground=STYLE_CONFIG["text_main"]).pack(anchor="w", pady=(0, 4))
        if video_url:
            def open_video():
                import webbrowser
                if "youtube.com" not in video_url:
                    url = f"https://www.youtube.com/watch?v={video_url}"
                else:
                    url = video_url
                webbrowser.open(url)
            ttk.Button(details_frame, text="Watch Video", style="Accent.TButton", command=open_video).pack(anchor="w", pady=(8, 0))

        # Instructions (spanning both columns)
        instr_label = ttk.Label(card, text="Instructions:", font=(STYLE_CONFIG["font_bold"], 15), background=STYLE_CONFIG["bg_panel"], foreground=STYLE_CONFIG["text_main"])
        instr_label.grid(row=2, column=1, sticky="nw", padx=(8, 24), pady=(8, 0))
        instr_frame = tk.Frame(card, bg=STYLE_CONFIG["bg_panel"])
        instr_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=(24, 24), pady=(0, 12))
        instr_text = tk.Text(instr_frame, wrap="word", font=(STYLE_CONFIG["font"], 12), bg=STYLE_CONFIG["bg_panel"], fg=STYLE_CONFIG["text_main"], bd=0, height=8, relief="flat", highlightthickness=0)
        instr_text.insert("1.0", instructions)
        instr_text.config(state="disabled")
        instr_text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(instr_frame, orient="vertical", command=instr_text.yview)
        scrollbar.pack(side="right", fill="y")
        instr_text.config(yscrollcommand=scrollbar.set)
        card.grid_rowconfigure(3, weight=1)
        card.grid_columnconfigure(1, weight=1)

        # Close button
        ttk.Button(card, text="Close", style="Secondary.TButton", command=self.destroy).grid(row=4, column=1, sticky="e", padx=(8, 24), pady=(8, 16))

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

    # def _filter_favorites(self):
    #     # Filter recipes by is_favorite for selected person needs to be implemented in the model/database first
    #     selected_person = self.person_var.get()
    #     if not selected_person:
    #         return
    #     filtered = [r for r in recipes if getattr(r, 'recipe_id', None) in fav_recipe_ids]
    #     self.recipe_listbox.delete(0, tk.END)
    #     for recipe in filtered:
    #         self.recipe_listbox.insert(tk.END, getattr(recipe, "recipe_name", "(Unnamed Recipe)"))

# Add more windows as needed
