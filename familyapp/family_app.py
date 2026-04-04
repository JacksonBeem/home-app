# Family subsystem UI: handles displaying members, favorites, and profile images
from operator import index
from random import choice
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext

from models.recipe import Recipe
from .family_model import get_favorite_by_id, get_favorites_for_person, writeprofilepicturetodb
from tkinter import filedialog
from PIL import Image, ImageTk
import io
from .family_model import get_all_members, add_member, delete_member, update_member
from banner import TopBanner

# Main UI class for displaying and managing family members
class FamilyPage(ttk.Frame):

    def __init__(self, master, *, on_home):
        from ui_style import STYLE_CONFIG
        super().__init__(master, padding=16)
        self.on_home = on_home
        self.member_photos = {}
        # self.configure(bg=STYLE_CONFIG["bg_main"])  # Not supported for ttk widgets
        self._build()
        self.refresh_list()

    # Builds the full layout: header, buttons, and scrollable member list
    def _build(self):
        # Consistent top banner
        TopBanner(self, title="Family Members", on_home=self.on_home).pack(side=tk.TOP, fill=tk.X)

        # Action buttons for member management and favorite food features
        from ui_style import STYLE_CONFIG
        buttons = ttk.Frame(self, style="Card.TFrame")
        buttons.pack(side=tk.TOP, pady=20)
        style = ttk.Style(self)
        style.configure("Card.TFrame", background=STYLE_CONFIG["bg_panel"], relief="flat", borderwidth=0)
        style.configure("TButton", font=(STYLE_CONFIG["button_font"], STYLE_CONFIG["button_font_size"]), padding=(10, 6))

        add_btn = ttk.Button(
            buttons,
            text="Add Member",
            style="TopNav.TButton",
            command=self._on_add_click
        )
        add_btn.grid(row=0, column=0, padx=10)

        delete_btn = ttk.Button(
            buttons,
            text="Delete Member",
            style="TopNav.TButton",
            command=self._on_delete_click
        )
        delete_btn.grid(row=0, column=1, padx=10)

        update_btn = ttk.Button(
            buttons,
        text="Update Member",
        style="TopNav.TButton",
        command=self._on_update_click
        )
        update_btn.grid(row=0, column=2, padx=10)

        favorite_btn = ttk.Button(
        buttons,
        text="Assign Favorite Food",
        style="TopNav.TButton",
        command=self._on_assign_favorite
        )
        favorite_btn.grid(row=0, column=3, padx=10)

        remove_fav_btn = ttk.Button(
        buttons,
        text="Remove Favorite Food",
        style="TopNav.TButton",
        command=self._on_remove_favorite
        )
        remove_fav_btn.grid(row=0, column=4, padx=10)
        # Scrollable container to hold all member cards
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Reloads and redraws all members and their data from the database
    def refresh_list(self):
        # Clear existing UI elements before rebuilding
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        # Fetch all members from database
        members = get_all_members()
        # Keep references to PhotoImage objects to avoid garbage collection
        self._photo_refs = {}
        for m in members:
            # Container box representing one member
            card = ttk.Frame(self.scrollable_frame, padding=15, relief="solid", borderwidth=1)
            card.pack(fill=tk.X, padx=40, pady=10)
            card.columnconfigure(1, weight=1)

            # Left side: profile image or upload button
            img_frame = ttk.Frame(card, width=170, height=170, relief="solid", borderwidth=1)
            img_frame.pack_propagate(False)
            img_frame.pack(side=tk.LEFT, padx=(40, 25))

            if m.profile_picture:
                img = Image.open(io.BytesIO(m.profile_picture))
                img = img.resize((170, 170), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._photo_refs[m.person_id] = photo
                img_label = tk.Label(img_frame, image=photo, bd=0, highlightthickness=0)
                img_label.place(x=0, y=0, relwidth=1, relheight=1)
            else:
                # Button to upload profile picture for this member
                upload_btn = ttk.Button(
                    img_frame,
                    text="Upload",
                    command=lambda pid=m.person_id: self._upload_photo(pid)
                )
                upload_btn.pack(expand=True)

            # Right side: member details and favorite foods
            info_frame = ttk.Frame(card)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            # Format member name and basic info with larger font
            name = f"{m.person_id}: {m.first_name} {m.last_name} ({m.gender})"
            ttk.Label(info_frame, text=name, font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 2))
            # Retrieve favorite foods for this member
            favorites = get_favorites_for_person(m.person_id)

            if favorites:
                ttk.Label(info_frame, text="Favorites:", font=("Segoe UI", 14, "italic")).pack(anchor="w")
                # Display numbered list of favorite foods with larger font
                for i, f in enumerate(favorites, start=1):
                    ttk.Label(info_frame, text=f"{i}.) {get_favorite_by_id(f.recipe_id)}", font=("Segoe UI", 13)).pack(anchor="w")

    # Handles adding a new member through user input
    def _on_add_click(self):

        parent = self.winfo_toplevel()

        first = simpledialog.askstring("First Name", "Enter first name:", parent=parent)
        if not first:
            return

        last = simpledialog.askstring("Last Name", "Enter last name:", parent=parent)
        if not last:
            return

        gender = simpledialog.askstring("Gender", "Enter gender:", parent=parent)
        if not gender:
            return

        add_member(first, last, gender)

        self.refresh_list()

    # Handles deleting a member and their related data
    def _on_delete_click(self):

        person_id = simpledialog.askinteger("Delete Member", "Enter Person ID:")

        if not person_id:
            return

        confirm = messagebox.askyesno(
        "Confirm",
        "This will delete the member AND all their favorites. Continue?"
)

        if confirm:
            success = delete_member(person_id)

            if success:
                self.refresh_list()
            else:
                messagebox.showerror("Error", "Member not found.")

    # Handles updating existing member information
    def _on_update_click(self):

        parent = self.winfo_toplevel()

        person_id = simpledialog.askinteger("Update Member", "Enter Person ID:", parent=parent)

        if not person_id:
            return

        first = simpledialog.askstring("First Name", "Enter new first name:", parent=parent)
        if not first:
            return

        last = simpledialog.askstring("Last Name", "Enter new last name:", parent=parent)
        if not last:
            return

        gender = simpledialog.askstring("Gender", "Enter new gender:", parent=parent)
        if not gender:
            return

        success = update_member(person_id, first, last, gender)

        if success:
            self.refresh_list()
        else:
            messagebox.showerror("Error", "Member not found.")

    # Adds a favorite food to a selected member
    def _on_assign_favorite(self):
        parent = self.winfo_toplevel()

        person_id = simpledialog.askinteger("Favorite Food", "Enter Person ID:", parent=parent)
        if not person_id:
            return

        # Import here to avoid circular imports
        from .family_model import getallrecipes, assign_favorite_food

        # Fetch all recipes
        recipes = getallrecipes()
        if not recipes:
            messagebox.showerror("Error", "No recipes found.")
            return

        # Create a dialog window for recipe selection
        dialog = tk.Toplevel(parent)
        dialog.title("Select Favorite Food")
        dialog.grab_set()

        tk.Label(dialog, text="Select favorite food:").pack(padx=10, pady=10)

        recipe_names = [r.recipe_name for r in recipes]
        recipe_ids = [r.recipe_id for r in recipes]

        selected_var = tk.StringVar(value=recipe_names[0])
        combo = ttk.Combobox(dialog, textvariable=selected_var, values=recipe_names, state="readonly")
        combo.pack(padx=10, pady=10)

        def on_ok():
            idx = recipe_names.index(selected_var.get())
            food_id = recipe_ids[idx]
            assign_favorite_food(person_id, food_id)
            dialog.destroy()
            self.refresh_list()
            messagebox.showinfo("Success", "Favorite added!")

        ok_btn = ttk.Button(dialog, text="OK", command=on_ok)
        ok_btn.pack(pady=(0, 10))

        dialog.wait_window()

    # Removes a specific favorite food based on user input
    def _on_remove_favorite(self):
        parent = self.winfo_toplevel()

        person_id = simpledialog.askinteger("Remove Favorite", "Enter Person ID:", parent=parent)
        if not person_id:
            return

        from .family_model import get_favorites_for_person, get_favorite_by_id, delete_favorite_by_id
        favorites = get_favorites_for_person(person_id)
        if not favorites:
            messagebox.showerror("Error", "No favorites found for this person.")
            return

        # Get display names for favorites
        favorite_names = [get_favorite_by_id(f.recipe_id) for f in favorites]

        dialog = tk.Toplevel(parent)
        dialog.title("Remove Favorite Food")
        dialog.grab_set()

        tk.Label(dialog, text="Select favorite food to remove:").pack(padx=10, pady=10)

        selected_var = tk.StringVar(value=favorite_names[0])
        combo = ttk.Combobox(dialog, textvariable=selected_var, values=favorite_names, state="readonly")
        combo.pack(padx=10, pady=10)

        def on_ok():
            idx = favorite_names.index(selected_var.get())
            food_id = favorites[idx].recipe_id
            success = delete_favorite_by_id(food_id)
            dialog.destroy()
            if success:
                self.refresh_list()
                messagebox.showinfo("Success", "Favorite removed!")
            else:
                messagebox.showerror("Error", "Delete failed.")

        ok_btn = ttk.Button(dialog, text="OK", command=on_ok)
        ok_btn.pack(pady=(0, 10))

        dialog.wait_window()

    # Allows user to upload and display a profile image
    def _upload_photo(self, person_id):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if not file_path:
            return

        img = Image.open(file_path)
        # Resize image to fit UI box properly
        img = img.resize((170, 170), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.member_photos[person_id] = photo

        # Save as PNG bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()
        writeprofilepicturetodb(person_id, img_bytes)

        self.refresh_list()