from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
from typing import Optional

from .chores_model import get_all_chores, add_chore, delete_chore, set_chore_priority, assign_chore_member

class ChoresPage(ttk.Frame):
    """"  
    Layout
        [create] [delete] [alert creation] [priority assignment] [assign member]
                                    [chore list]
    """
    def __init__(self, master: tk.Misc, *, on_home):
        super().__init__(master)
        self.on_home = on_home
        self._build()
        self.refresh_list()
   
    def _build(self) -> None:
        # 1. Header Frame
        header = ttk.Frame(self)
        header.pack(side=tk.TOP, fill=tk.X)

        # 2. Back/Home Button
        if self.on_home:
            back_btn = ttk.Button(
                header, 
                text="← Home", 
                style="TopNav.TButton",
                command=self.on_home
            )
            back_btn.pack(side=tk.LEFT)

        title = ttk.Label(header, text="House Chores", style="Title.TLabel")
        title.pack(side=tk.LEFT, padx=(20, 0))

        tiles_outer = ttk.Frame(self)
        tiles_outer.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(22, 0))

        tiles = ttk.Frame(tiles_outer, style="Card.TFrame", padding=18)
        tiles.pack(side=tk.LEFT, anchor="n")

        tile_w = 9
        tile_h = 3

        def tile(text: str, key: str, style: str = "Tile.TButton"):
            return ttk.Button(
                tiles,
                text=text,
                style=style,
                width=tile_w,
                command=lambda: self.on_open(key),
            )

        btn_create = ttk.Button(tiles, text="Create", style="Tile.TButton", width=tile_w,
            command=self._on_create_click)
        btn_alert = ttk.Button(tiles, text="Create Alert", style="Tile.TButton", width=tile_w,
            command=self._on_alert_click)
        btn_assign = ttk.Button(tiles, text="Assign Mem", style="Tile.TButton", width=tile_w,
            command=self._on_assign_click)
        btn_delete = ttk.Button(tiles, text="Delete", style="Tile.TButton", width=tile_w,
            command=self._on_delete_click
        )
        btn_priority = ttk.Button(tiles, text="Set Priority", style="Tile.TButton", width=tile_w, 
            command=self._on_priority_click
        )

        btn_create.grid(row=0, column=0, padx=4, pady=4, ipadx=8, ipady=tile_h)
        btn_delete.grid(row=0, column=1, padx=4, pady=4, ipadx=8, ipady=tile_h)
        btn_alert.grid(row=0, column=2, padx=4, pady=4, ipadx=8, ipady=tile_h)
        btn_priority.grid(row=0, column=3, padx=4, pady=4, ipadx=8, ipady=tile_h)
        btn_assign.grid(row=0, column=4, padx=4, pady=4, ipadx=8, ipady=tile_h)

        
        self.chore_list = scrolledtext.ScrolledText(tiles, width=80, height=10)
        self.chore_list.grid(row=1, column=0, columnspan=5, padx=10, pady=10)

        self.chore_list.tag_config("prio1", background="#ffcccc", foreground="black")
        self.chore_list.tag_config("prio2", background="#ffffcc", foreground="black")
        self.chore_list.tag_config("prio3", background="#ccffcc", foreground="black")
    
    def refresh_list(self):
        self.chore_list.configure(state='normal')
        self.chore_list.delete('1.0', tk.END)
        
        chores = get_all_chores()
        
        for c in chores:
            # Change c.id to c.chore_id
            display_text = f"#{c.chore_num:<3} | {c.description} | Assigned to: {c.person_id} | Prio: {c.priority}\n"
            self.chore_list.insert(tk.END, display_text)
            
        self.chore_list.configure(state='disabled')
    
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