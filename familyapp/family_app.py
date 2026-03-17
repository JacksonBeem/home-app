import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext

from .family_model import get_all_members, add_member, delete_member, update_member


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


        self.member_list = scrolledtext.ScrolledText(self, width=80, height=15)
        self.member_list.pack(pady=10)

    def refresh_list(self):

        self.member_list.configure(state='normal')
        self.member_list.delete('1.0', tk.END)

        members = get_all_members()

        for m in members:
            text = f"{m.person_id}: {m.first_name} {m.last_name} ({m.gender})\n"
            self.member_list.insert(tk.END, text)

        self.member_list.configure(state='disabled')

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

        confirm = messagebox.askyesno("Confirm", f"Delete member {person_id}?")

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
            