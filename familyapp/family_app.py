from operator import index
from random import choice
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext
from .family_model import get_favorites_for_person

from .family_model import assign_reminder, get_all_members, add_member, delete_member, update_member, get_reminders_for_person
class FamilyPage(ttk.Frame):

    def __init__(self, master, *, on_home):
        super().__init__(master)
        self.on_home = on_home
        self._build()
        self.refresh_list()

    def _build(self):

        header = ttk.Frame(self)
        header.pack(side=tk.TOP, fill=tk.X)

        back_btn = ttk.Button(
            header,
            text="← Home",
            style="TopNav.TButton",
            command=self.on_home
        )
        back_btn.pack(side=tk.LEFT)

        title = ttk.Label(header, text="Family Members", style="Title.TLabel")
        title.pack(side=tk.LEFT, padx=(20, 0))

        buttons = ttk.Frame(self)
        buttons.pack(side=tk.TOP, pady=20)

        add_btn = ttk.Button(
            buttons,
            text="Add Member",
            command=self._on_add_click
        )
        add_btn.grid(row=0, column=0, padx=10)

        delete_btn = ttk.Button(
            buttons,
            text="Delete Member",
            command=self._on_delete_click
        )
        delete_btn.grid(row=0, column=1, padx=10)

        update_btn = ttk.Button(
            buttons,
        text="Update Member",
        command=self._on_update_click
        )
        update_btn.grid(row=0, column=2, padx=10)

        reminder_btn = ttk.Button(
            buttons,
        text="Assign Reminder",
        command=self._on_assign_reminder
        )   
        reminder_btn.grid(row=0, column=3, padx=10)

        delete_reminder_btn = ttk.Button(
            buttons,
            text="Delete Reminder",
            command=self._on_delete_reminder
        )
        delete_reminder_btn.grid(row=0, column=4, padx=10)

        favorite_btn = ttk.Button(
        buttons,
        text="Assign Favorite Food",
        command=self._on_assign_favorite
        )
        favorite_btn.grid(row=0, column=5, padx=10)


        self.member_list = scrolledtext.ScrolledText(self, width=65, height=15)
        self.member_list.pack(pady=10)

    def refresh_list(self):

        self.member_list.configure(state='normal')
        self.member_list.delete('1.0', tk.END)

        self.member_list.tag_config("name", font=("Segoe UI", 13, "bold"))
        self.member_list.tag_config("normal", font=("Segoe UI", 12))
        self.member_list.tag_config("section", font=("Segoe UI", 12, "italic"))
        
        members = get_all_members()

        for m in members:
            text = f"{m.person_id}: {m.first_name} {m.last_name} ({m.gender})\n"
            self.member_list.insert(tk. END, text, "name")
            
            reminders = get_reminders_for_person(m.person_id)

            if reminders:
                self.member_list.insert(tk.END, "   Reminders:\n", "section")

            for i, r in enumerate(reminders, start=1):
                reminder_text = f"      {i}.) {r.description} ({r.frequency})\n"
                self.member_list.insert(tk.END, reminder_text, "normal")


            # Favorites
            favorites = get_favorites_for_person(m.person_id)

            if favorites:
                self.member_list.insert(tk.END, " ")
                self.member_list.insert(tk.END, "   Favorites:\n", "section")

            for f in favorites:
                fav_text = f"      • {f.food_name}\n"
                self.member_list.insert(tk.END, fav_text, "normal")

            self.member_list.insert(tk.END, " ")

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

    def _on_delete_click(self):

        person_id = simpledialog.askinteger("Delete Member", "Enter Person ID:")

        if not person_id:
            return

        confirm = messagebox.askyesno(
        "Confirm",
        "This will delete the member AND all their reminders and favorites. Continue?"
)

        if confirm:
            success = delete_member(person_id)

            if success:
                self.refresh_list()
            else:
                messagebox.showerror("Error", "Member not found.")

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

    def _on_assign_reminder(self):

        parent = self.winfo_toplevel()

        person_id = simpledialog.askinteger("Assign Reminder", "Enter Person ID:", parent=parent)
        if not person_id:
            return

        description = simpledialog.askstring("Reminder", "Enter reminder description:", parent=parent)
        if not description:
            return

        frequency = self._choose_frequency()
        if not frequency:
            return

        assign_reminder(person_id, description, frequency)

        self.refresh_list()

        messagebox.showinfo("Success", "Reminder assigned!")

    def _choose_frequency(self):

        choice = {"value": None}

        win = tk.Toplevel(self)
        win.title("Select Frequency")

        width = 315
        height = 210

        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        win.geometry(f"{width}x{height}+{x}+{y}")

        label = ttk.Label(win, text="Select Frequency:", font=("Segoe UI", 12))
        label.pack(pady=15)

        def set_freq(val):
            choice["value"] = val
            win.destroy()

        ttk.Button(win, text="Daily", width=20, command=lambda: set_freq("Daily")).pack(pady=5)
        ttk.Button(win, text="Weekly", width=20, command=lambda: set_freq("Weekly")).pack(pady=5)
        ttk.Button(win, text="Monthly", width=20, command=lambda: set_freq("Monthly")).pack(pady=5)

        self.wait_window(win)

        return choice["value"]

    def _on_delete_reminder(self):

        parent = self.winfo_toplevel()

        person_id = simpledialog.askinteger("Delete Reminder", "Enter Person ID:", parent=parent)
        if not person_id:
            return

        reminder_num = simpledialog.askinteger("Delete Reminder", "Enter reminder number:", parent=parent)
        if not reminder_num:
            return

        from .family_model import get_reminders_for_person, delete_reminder_by_id

        reminders = get_reminders_for_person(person_id)

        if reminder_num < 1 or reminder_num > len(reminders):
            messagebox.showerror("Error", "Invalid reminder number")
            return

        reminder = reminders[reminder_num - 1]

        success = delete_reminder_by_id(reminder.chore_id)

        if success:
            self.refresh_list()
            messagebox.showinfo("Success", "Reminder deleted!")
        else:
            messagebox.showerror("Error", "Delete failed.")

    def _on_assign_favorite(self):

        parent = self.winfo_toplevel()

        person_id = simpledialog.askinteger("Favorite Food", "Enter Person ID:", parent=parent)
        if not person_id:
            return

        food = simpledialog.askstring("Favorite Food", "Enter favorite food:", parent=parent)
        if not food:
            return

        from .family_model import assign_favorite_food

        assign_favorite_food(person_id, food)

        self.refresh_list()

        messagebox.showinfo("Success", "Favorite added!")