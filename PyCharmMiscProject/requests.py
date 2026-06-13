import tkinter as tk
from tkinter import ttk, messagebox
import database


def create_requests_window(root, user, go_back):
    """Create blood requests window"""
    clear_window(root)

    root.title("Blood Donation System - Blood Requests")

    # Title
    tk.Label(root, text="Blood Requests", font=("Arial", 20, "bold"),
             bg="#f0f0f0").pack(pady=10)

    # Table frame
    table_frame = tk.Frame(root)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Create treeview
    columns = ("Request ID", "Blood Type", "Units", "Request Date", "Status")
    requests_tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", height=15)

    col_widths = [100, 100, 80, 120, 100]
    for col, width in zip(columns, col_widths):
        requests_tree.heading(col, text=col)
        requests_tree.column(col, width=width)

    # Scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                              command=requests_tree.yview)
    requests_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    requests_tree.pack(fill=tk.BOTH, expand=True)

    def load_requests():
        """Load requests into treeview"""
        # Clear existing items
        for item in requests_tree.get_children():
            requests_tree.delete(item)

        requests = database.get_blood_requests()

        if requests:
            for req in requests:
                requests_tree.insert("", tk.END, values=(
                    req['request_id'],
                    req['blood_type'],
                    req['units'],
                    req['request_date'],
                    req['status']
                ))

    # Load initial data
    load_requests()

    def new_request_func():
        """Create new blood request"""
        request_window = tk.Toplevel(root)
        request_window.title("New Blood Request")
        request_window.geometry("400x250")

        tk.Label(request_window, text="New Blood Request",
                 font=("Arial", 16, "bold")).pack(pady=20)

        # Form
        form_frame = tk.Frame(request_window)
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

        tk.Label(form_frame, text="Units Required:", font=("Arial", 11)
                 ).grid(row=1, column=0, pady=10, sticky=tk.E)

        units_var = tk.StringVar()
        units_entry = tk.Entry(form_frame, textvariable=units_var, font=("Arial", 11))
        units_entry.grid(row=1, column=1, pady=10, padx=10)

        def save_request():
            """Save blood request"""
            try:
                blood_type = blood_type_var.get()
                units = int(units_var.get())

                if units <= 0:
                    messagebox.showwarning("Invalid Input", "Please enter a positive number")
                    return

                # Check inventory
                available = database.get_blood_units(blood_type)
                if units > available:
                    messagebox.showwarning("Insufficient Stock",
                                           f"Only {available} units of {blood_type} available")
                    return

                result = database.create_blood_request(blood_type, units)
                if result:
                    messagebox.showinfo("Success", "Blood request created successfully")
                    request_window.destroy()
                    load_requests()
                else:
                    messagebox.showerror("Error", "Failed to create request")

            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid number")

        # Buttons
        button_frame = tk.Frame(request_window)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Submit Request",
                  font=("Arial", 11, "bold"),
                  bg="#4CAF50", fg="white", command=save_request
                  ).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="Cancel", font=("Arial", 11),
                  bg="#757575", fg="white", command=request_window.destroy
                  ).pack(side=tk.LEFT, padx=10)

    def approve_request_func():
        """Approve selected request"""
        selection = requests_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a request")
            return

        request_id = requests_tree.item(selection[0])['values'][0]
        blood_type = requests_tree.item(selection[0])['values'][1]
        units = requests_tree.item(selection[0])['values'][2]

        # Check if enough blood is available
        available = database.get_blood_units(blood_type)
        if available < units:
            messagebox.showwarning("Insufficient Stock",
                                   f"Only {available} units of {blood_type} available")
            return

        confirm = messagebox.askyesno("Confirm Approval",
                                      f"Approve request for {units} units of {blood_type}?")

        if confirm:
            result = database.fulfill_request(request_id, blood_type, units)
            if result:
                messagebox.showinfo("Success", "Request approved and inventory updated")
                load_requests()
            else:
                messagebox.showerror("Error", "Failed to approve request")

    def reject_request_func():
        """Reject selected request"""
        selection = requests_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a request")
            return

        request_id = requests_tree.item(selection[0])['values'][0]
        blood_type = requests_tree.item(selection[0])['values'][1]
        units = requests_tree.item(selection[0])['values'][2]

        confirm = messagebox.askyesno("Confirm Rejection",
                                      f"Reject request for {units} units of {blood_type}?")

        if confirm:
            result = database.update_request_status(request_id, 'Rejected')
            if result:
                messagebox.showinfo("Success", "Request rejected")
                load_requests()
            else:
                messagebox.showerror("Error", "Failed to reject request")

    # Action buttons
    action_frame = tk.Frame(root, bg="#f0f0f0")
    action_frame.pack(pady=10)

    buttons = [
        ("New Request", new_request_func, "#388E3C"),
        ("Approve Request", approve_request_func, "#4CAF50"),
        ("Reject Request", reject_request_func, "#f44336"),
        ("Refresh", load_requests, "#2196F3"),
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