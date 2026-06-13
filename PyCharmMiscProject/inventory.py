import tkinter as tk
from tkinter import ttk, messagebox
import database


def create_inventory_window(root, user, go_back):
    """Create inventory window"""
    clear_window(root)

    root.title("Blood Donation System - Blood Inventory")

    # Title
    tk.Label(root, text="Blood Inventory", font=("Arial", 20, "bold"),
             bg="#f0f0f0").pack(pady=10)

    # Stats frame
    stats = database.get_dashboard_stats()
    stats_frame = tk.Frame(root, bg="#ffffff", relief=tk.RAISED, bd=1)
    stats_frame.pack(fill=tk.X, padx=20, pady=10)

    total_units = stats['total_blood_units']
    tk.Label(stats_frame, text=f"Total Blood Units Available: {total_units}",
             font=("Arial", 14, "bold"), bg="#ffffff", fg="#d32f2f"
             ).pack(pady=10)

    # Table frame
    table_frame = tk.Frame(root)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Create treeview
    columns = ("Blood Type", "Units Available")
    inventory_tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", height=10)

    inventory_tree.heading("Blood Type", text="Blood Type")
    inventory_tree.heading("Units Available", text="Units Available")
    inventory_tree.column("Blood Type", width=150)
    inventory_tree.column("Units Available", width=150)

    # Scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                              command=inventory_tree.yview)
    inventory_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    inventory_tree.pack(fill=tk.BOTH, expand=True)

    def load_inventory():
        """Load inventory into treeview"""
        # Clear existing items
        for item in inventory_tree.get_children():
            inventory_tree.delete(item)

        inventory = database.get_inventory()

        for item in inventory:
            inventory_tree.insert("", tk.END, values=(
                item['blood_type'],
                item['units']
            ))

    # Load initial data
    load_inventory()

    def add_blood_units_func():
        """Open add blood units form"""
        add_window = tk.Toplevel(root)
        add_window.title("Add Blood Units")
        add_window.geometry("400x250")

        tk.Label(add_window, text="Add Blood Units to Inventory",
                 font=("Arial", 16, "bold")).pack(pady=20)

        # Form
        form_frame = tk.Frame(add_window)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Blood Type:", font=("Arial", 11)
                 ).grid(row=0, column=0, pady=10, sticky=tk.E)

        blood_type_var = tk.StringVar()
        blood_type_combo = ttk.Combobox(
            form_frame,
            textvariable=blood_type_var,
            values=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            state="readonly",
            width=20
        )
        blood_type_combo.grid(row=0, column=1, pady=10, padx=10)
        blood_type_combo.current(0)

        tk.Label(form_frame, text="Units to Add:", font=("Arial", 11)
                 ).grid(row=1, column=0, pady=10, sticky=tk.E)

        units_var = tk.StringVar()
        units_entry = tk.Entry(form_frame, textvariable=units_var, font=("Arial", 11))
        units_entry.grid(row=1, column=1, pady=10, padx=10)

        def save_units():
            """Save blood units to inventory"""
            try:
                blood_type = blood_type_var.get()
                units = int(units_var.get())

                if units <= 0:
                    messagebox.showwarning("Invalid Input", "Please enter a positive number")
                    return

                result = database.update_inventory(blood_type, units)
                if result:
                    messagebox.showinfo("Success",
                                        f"{units} units of {blood_type} added to inventory")
                    add_window.destroy()
                    load_inventory()
                else:
                    messagebox.showerror("Error", "Failed to update inventory")

            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid number")

        # Buttons
        button_frame = tk.Frame(add_window)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Add to Inventory",
                  font=("Arial", 11, "bold"),
                  bg="#4CAF50", fg="white", command=save_units
                  ).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="Cancel", font=("Arial", 11),
                  bg="#757575", fg="white", command=add_window.destroy
                  ).pack(side=tk.LEFT, padx=10)

    # Action buttons
    action_frame = tk.Frame(root, bg="#f0f0f0")
    action_frame.pack(pady=10)

    buttons = [
        ("Add Blood Units", add_blood_units_func, "#388E3C"),
        ("Refresh", load_inventory, "#2196F3"),
        ("Back to Dashboard", go_back, "#757575")
    ]

    for text, command, color in buttons:
        tk.Button(action_frame, text=text, font=("Arial", 10),
                  bg=color, fg="white", command=command
                  ).pack(side=tk.LEFT, padx=5)


def clear_window(root):
    """Clear all widgets from window"""
    for widget in root.winfo_children():
        widget.destroy()