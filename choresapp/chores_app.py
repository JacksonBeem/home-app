from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
from typing import Optional


from .chores_model import get_all_chores, add_chore, delete_chore, set_chore_priority, assign_chore_member
from banner import TopBanner

class ChoresPage(ttk.Frame):
    """"  
    Layout
        [create] [delete] [alert creation] [priority assignment] [assign member]
                                    [chore list]
    """
    def __init__(self, master: tk.Misc, *, on_home):
        from ui_style import STYLE_CONFIG
        super().__init__(master, padding=16)
        self.on_home = on_home
        # self.configure(bg=STYLE_CONFIG["bg_main"])  # Not supported for ttk widgets
        self._build()
        self.refresh_list()
   
    def _build(self) -> None:
        # Consistent top banner
        TopBanner(self, title="House Chores", on_home=self.on_home).pack(side=tk.TOP, fill=tk.X)

        from ui_style import STYLE_CONFIG
        tiles_outer = ttk.Frame(self, style="Card.TFrame")
        tiles_outer.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(22, 0))

        style = ttk.Style(self)
        style.configure("Card.TFrame", background=STYLE_CONFIG["bg_panel"], relief="flat", borderwidth=0)

        tiles = ttk.Frame(tiles_outer, style="Card.TFrame", padding=18)
        tiles.pack(side=tk.LEFT, anchor="n")

        # Use Accent/Secondary.TButton styles for consistency
        btn_create = ttk.Button(tiles, text="Create", style="Accent.TButton", width=14, command=self._on_create_click)
        btn_delete = ttk.Button(tiles, text="Delete", style="Secondary.TButton", width=14, command=self._on_delete_click)
        btn_alert = ttk.Button(tiles, text="Create Alert", style="Secondary.TButton", width=14, command=self._on_alert_click)
        btn_priority = ttk.Button(tiles, text="Set Priority", style="Secondary.TButton", width=14, command=self._on_priority_click)
        btn_assign = ttk.Button(tiles, text="Assign Mem", style="Secondary.TButton", width=14, command=self._on_assign_click)

        btn_create.grid(row=0, column=0, padx=6, pady=6)
        btn_delete.grid(row=0, column=1, padx=6, pady=6)
        btn_alert.grid(row=0, column=2, padx=6, pady=6)
        btn_priority.grid(row=0, column=3, padx=6, pady=6)
        btn_assign.grid(row=0, column=4, padx=6, pady=6)

        
        # Modern Treeview for chore list
        columns = ("num", "desc", "person", "prio")
        self.chore_tree = ttk.Treeview(tiles, columns=columns, show="headings", style="Custom.Treeview", height=10)
        self.chore_tree.heading("num", text="#")
        self.chore_tree.heading("desc", text="Description")
        self.chore_tree.heading("person", text="Assigned To")
        self.chore_tree.heading("prio", text="Priority")
        self.chore_tree.column("num", width=40, anchor="center")
        self.chore_tree.column("desc", width=320, anchor="w")
        self.chore_tree.column("person", width=120, anchor="center")
        self.chore_tree.column("prio", width=80, anchor="center")
        self.chore_tree.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")
        # Add vertical scrollbar
        tree_scroll = ttk.Scrollbar(tiles, orient="vertical", command=self.chore_tree.yview)
        tree_scroll.grid(row=1, column=5, sticky="ns")
        self.chore_tree.configure(yscrollcommand=tree_scroll.set)
    
    def refresh_list(self):
        # Clear the treeview
        for row in self.chore_tree.get_children():
            self.chore_tree.delete(row)
        chores = get_all_chores()
        for c in chores:
            prio = str(c.priority)
            self.chore_tree.insert("", "end", values=(c.chore_num, c.description, c.person_id, prio))
    
    def _on_create_click(self):
        # 1. Collect data from user

        parent = self.winfo_toplevel()
        while True:
            desc = simpledialog.askstring("New Chore", "What is the chore description?", parent=parent)
            if desc is None or desc.strip() != "":
                break
        if desc is None:
            return  # User cancelled

        while True:
            p_id = simpledialog.askinteger("Assign", "Enter Person ID (Number):", parent=parent)
            if p_id is None or str(p_id).strip() != "":
                break
        if p_id is None:
            return  # User cancelled

        while True:
            freq = simpledialog.askstring("Frequency", "How often? (Daily, Weekly, etc.):", parent=parent)
            if freq is None or freq.strip() != "":
                break
        if freq is None:
            return  # User cancelled

        # 2. Send to chores_model.py
        try:
            success = add_chore(description=desc, person_id=p_id, frequency=freq)
            if success:
                # 3. Update the UI to show the new data
                self.refresh_list()
                messagebox.showinfo("Success", "Chore added successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not add chore: {e}")

    def _on_delete_click(self):
        # 1. Ask the user which ID to delete
        target_id = simpledialog.askinteger("Delete Chore", "Enter the Chore ID to remove:")
        
        if target_id:
            # 2. Confirm with the user
            confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete chore #{target_id}?")
            
            if confirm:
                # 3. Call the model
                success = delete_chore(target_id)
                
                if success:
                    # 4. Refresh the UI
                    self.refresh_list()
                else:
                    messagebox.showerror("Error", f"Chore ID {target_id} not found.")

    def _on_priority_click(self):
        # 1. Ask which chore to update
        target_num = simpledialog.askinteger("Priority", "Enter Chore #:")
        if target_num is None: return

        # 2. Ask for the new priority level
        new_prio = simpledialog.askinteger("Priority", "Enter Level (1=Critical, 2=Non-Critical, 3=Important, 0=When Needed):")
        
        if new_prio is not None:
            if 0 <= new_prio <= 3:
                success = set_chore_priority(target_num, new_prio)
                if success:
                    self.refresh_list()
                else:
                    messagebox.showwarning("Error", f"Chore #{target_num} not found.")
            else:
                messagebox.showwarning("Invalid", "Please enter a priority between 0 and 3.")

    def _on_assign_click(self):
        # 1. Ask which chore to reassign
        target_num = simpledialog.askinteger("Assign Member", "Enter Chore #:")
        if target_num is None: return

        # 2. Ask for the new Person ID
        new_user_id = simpledialog.askinteger("Assign Member", "Enter New Person ID Number:")
        
        if new_user_id is not None:
            success = assign_chore_member(target_num, new_user_id)
            if success:
                self.refresh_list()
                messagebox.showinfo("Success", f"Chore #{target_num} reassigned to Person {new_user_id}")
            else:
                messagebox.showwarning("Error", f"Chore #{target_num} not found.")

    def _on_alert_click(self):
        # This provides feedback that the long-term chores are now synced to the dashboard
        chores = get_all_chores()
        
        # Check if there are any eligible chores to alert the user
        eligible = [c for c in chores if c.frequency and "daily" not in c.frequency.lower()]
        
        if eligible:
            messagebox.showinfo("Alerts Created", f"{len(eligible)} weekly/monthly chores added to Dashboard alerts.")
            # Navigate home to see the new list
            if self.on_home:
                self.on_home()
        else:
            messagebox.showwarning("No Alerts", "No chores found with Weekly or longer frequency.")