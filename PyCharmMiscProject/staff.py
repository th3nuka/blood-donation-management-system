import tkinter as tk
from tkinter import ttk, messagebox
import database


def create_staff_window(root, user, go_back):
    """Create staff management window"""

    clear_window(root)

    root.title("Blood Donation System - Manage Staff")
    root.geometry("1100x600")

    # Main container
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Title with Back button
    title_frame = tk.Frame(main_frame, bg="#f0f0f0")
    title_frame.pack(fill=tk.X, pady=(0, 20))

    tk.Button(title_frame, text="Back to Dashboard",
              font=("Arial", 10, "bold"), bg="#d32f2f", fg="white",
              width=20, command=go_back).pack(side=tk.LEFT)

    tk.Label(title_frame, text="Staff Management",
             font=("Arial", 24, "bold"), bg="#f0f0f0"
             ).pack(side=tk.LEFT, expand=True)

    # Stats frame
    stats_frame = tk.Frame(main_frame, bg="#ffffff", relief=tk.RAISED, bd=1)
    stats_frame.pack(fill=tk.X, pady=(0, 20))

    staff_count = len(database.get_all_staff()) if database.get_all_staff() else 0
    tk.Label(stats_frame, text=f"Total Staff Members: {staff_count}",
             font=("Arial", 14, "bold"), bg="#ffffff", fg="#388E3C"
             ).pack(pady=10)

    # Table frame
    table_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, bd=1)
    table_frame.pack(fill=tk.BOTH, expand=True)

    # Create treeview
    columns = ("ID", "Username", "Role")
    staff_tree = ttk.Treeview(table_frame, columns=columns,
                              show="headings", height=15)

    # Configure columns
    col_widths = [80, 250, 150]
    for col, width in zip(columns, col_widths):
        staff_tree.heading(col, text=col)
        staff_tree.column(col, width=width, anchor=tk.CENTER)

    # Scrollbars
    y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                command=staff_tree.yview)
    staff_tree.configure(yscrollcommand=y_scrollbar.set)
    y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    staff_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def load_staff():
        """Load staff into treeview"""
        # Clear existing items
        for item in staff_tree.get_children():
            staff_tree.delete(item)

        # Get staff from database
        staff_list = database.get_all_staff()

        if staff_list:
            for staff_member in staff_list:
                staff_tree.insert("", tk.END, values=(
                    staff_member['user_id'],
                    staff_member['username'],
                    staff_member['role']
                ))
            status_label.config(text=f"Showing {len(staff_list)} staff members", fg="#4CAF50")
        else:
            status_label.config(text="No staff members found", fg="#FF9800")

    # Status label
    status_label = tk.Label(main_frame, text="", font=("Arial", 11),
                            bg="#f0f0f0", fg="#4CAF50")
    status_label.pack(pady=(10, 0))

    # Load initial data
    load_staff()

    # Action buttons
    action_frame = tk.Frame(main_frame, bg="#f0f0f0")
    action_frame.pack(pady=20)

    def add_staff_func():
        """Open add staff form"""
        show_staff_form()

    def edit_staff_func():
        """Edit selected staff"""
        selection = staff_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a staff member to edit")
            return

        user_id = staff_tree.item(selection[0])['values'][0]
        show_staff_form(user_id)

    def delete_staff_func():
        """Delete selected staff"""
        selection = staff_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a staff member to delete")
            return

        user_id = staff_tree.item(selection[0])['values'][0]
        username = staff_tree.item(selection[0])['values'][1]

        # Prevent deleting your own account
        current_user_id = user.get('user_id')
        if current_user_id and str(user_id) == str(current_user_id):
            messagebox.showerror("Error", "You cannot delete your own account!")
            return

        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Are you sure you want to delete staff member:\n\n"
                                      f"Username: {username}\n"
                                      f"ID: {user_id}\n\n"
                                      "This action cannot be undone!")

        if confirm:
            result = database.delete_staff_member(user_id)
            if result:
                messagebox.showinfo("Success", "Staff member deleted successfully")
                load_staff()
            else:
                messagebox.showerror("Error", "Failed to delete staff member")

    # Button texts without icons
    buttons = [
        ("Add New Staff", add_staff_func, "#388E3C"),
        ("Edit Staff", edit_staff_func, "#FF9800"),
        ("Delete Staff", delete_staff_func, "#f44336"),
        ("Refresh", load_staff, "#2196F3"),
        ("Back to Dashboard", go_back, "#757575")
    ]

    for text, command, color in buttons:
        tk.Button(action_frame, text=text, font=("Arial", 10),
                  bg=color, fg="white", command=command
                  ).pack(side=tk.LEFT, padx=5)

    def show_staff_form(user_id=None):
        """Show staff form for add/edit"""
        form_window = tk.Toplevel(root)

        # Set title based on action
        if user_id:
            form_window.title("Edit Staff Member")
            action_text = "Edit"
        else:
            form_window.title("Add New Staff Member")
            action_text = "Add"

        form_window.geometry("400x350")
        form_window.resizable(False, False)

        # Make the form window modal
        form_window.transient(root)
        form_window.grab_set()

        # Main container frame
        main_frame = tk.Frame(form_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_text = f"{action_text} Staff Member"
        tk.Label(main_frame, text=title_text,
                 font=("Arial", 16, "bold")).pack(pady=(0, 10))

        # Form fields container
        form_fields = tk.Frame(main_frame)
        form_fields.pack(fill=tk.BOTH, expand=True)

        # Username field
        username_frame = tk.Frame(form_fields)
        username_frame.pack(fill=tk.X, pady=10)

        tk.Label(username_frame, text="Username:",
                 font=("Arial", 11), width=10, anchor=tk.W).pack(side=tk.LEFT)

        username_var = tk.StringVar()
        username_entry = tk.Entry(username_frame, textvariable=username_var,
                                  font=("Arial", 11), width=25)
        username_entry.pack(side=tk.LEFT, padx=(10, 0))
        username_entry.focus()

        # Password field
        password_frame = tk.Frame(form_fields)
        password_frame.pack(fill=tk.X, pady=10)

        tk.Label(password_frame, text="Password:",
                 font=("Arial", 11), width=10, anchor=tk.W).pack(side=tk.LEFT)

        password_var = tk.StringVar()
        password_entry = tk.Entry(password_frame, textvariable=password_var,
                                  font=("Arial", 11), width=25, show="*")
        password_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Role field
        role_frame = tk.Frame(form_fields)
        role_frame.pack(fill=tk.X, pady=10)

        tk.Label(role_frame, text="Role:",
                 font=("Arial", 11), width=10, anchor=tk.W).pack(side=tk.LEFT)

        role_var = tk.StringVar(value="staff")
        role_combo = ttk.Combobox(
            role_frame,
            textvariable=role_var,
            values=["admin", "staff"],
            state="readonly",
            width=23
        )
        role_combo.pack(side=tk.LEFT, padx=(10, 0))

        # Load data if editing
        if user_id:
            # Find staff in treeview
            for item in staff_tree.get_children():
                if staff_tree.item(item)['values'][0] == user_id:
                    staff_data = staff_tree.item(item)['values']
                    break

            if staff_data:
                username_var.set(staff_data[1])
                role_var.set(staff_data[2])
                password_entry.insert(0, "(Keep current password)")

        def save_staff():
            """Save staff data"""
            username = username_var.get().strip()
            password = password_var.get().strip()
            role = role_var.get()

            if not username:
                messagebox.showwarning("Validation Error", "Please enter username")
                username_entry.focus()
                return

            # For new staff, password is required
            if not user_id and not password:
                messagebox.showwarning("Validation Error", "Please enter password")
                password_entry.focus()
                return

            try:
                if user_id:
                    # EDITING existing staff member
                    # If password field has placeholder, don't update password
                    if password == "(Keep current password)":
                        password = ""
                        result = database.update_staff_member(user_id, username, "", role)
                    else:
                        result = database.update_staff_member(user_id, username, password, role)

                    if result:
                        messagebox.showinfo("Success", f"Staff member '{username}' updated successfully!")
                        form_window.destroy()
                        load_staff()
                    else:
                        messagebox.showerror("Error",
                                             f"Failed to update staff member.\n"
                                             f"Possible issues:\n"
                                             f"1. Username '{username}' already exists\n"
                                             f"2. Database connection error\n"
                                             f"3. User ID {user_id} not found")

                else:
                    # ADDING new staff member
                    result = database.add_staff_member(username, password, role)

                    if result:
                        messagebox.showinfo("Success", f"New staff member '{username}' added successfully!")
                        form_window.destroy()
                        load_staff()
                    else:
                        messagebox.showerror("Error",
                                             f"Failed to add staff member.\n"
                                             f"Possible issues:\n"
                                             f"1. Username '{username}' already exists\n"
                                             f"2. Database connection error")

            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred:\n{str(e)}")
                print(f"ERROR in save_staff: {e}")

        # Buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Save",
                  font=("Arial", 11, "bold"),
                  bg="#4CAF50", fg="white", width=15,
                  command=save_staff).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="Cancel", font=("Arial", 11),
                  bg="#757575", fg="white", width=15,
                  command=form_window.destroy).pack(side=tk.LEFT, padx=10)

    # End of show_staff_form function


def clear_window(root):
    """Clear all widgets from window"""
    for widget in root.winfo_children():
        widget.destroy()