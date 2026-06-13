import tkinter as tk
from tkinter import messagebox
import database


def create_login_window(root, on_login_success):
    """Create login window"""
    clear_window(root)

    root.title("Blood Donation System - Login")
    root.geometry("400x300")
    root.configure(bg="#f0f0f0")

    # Main frame
    main_frame = tk.Frame(root, bg="#ffffff", relief=tk.RAISED, bd=2)
    main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    # Title
    tk.Label(main_frame, text="Blood Donation System",
             font=("Arial", 18, "bold"), bg="#ffffff", fg="#d32f2f"
             ).grid(row=0, column=0, columnspan=2, pady=(20, 30), padx=30)

    # Username
    tk.Label(main_frame, text="Username:", font=("Arial", 12),
             bg="#ffffff").grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
    username_entry = tk.Entry(main_frame, font=("Arial", 12), width=25)
    username_entry.grid(row=1, column=1, padx=10, pady=10)
    username_entry.focus()

    # Password
    tk.Label(main_frame, text="Password:", font=("Arial", 12),
             bg="#ffffff").grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
    password_entry = tk.Entry(main_frame, font=("Arial", 12),
                              show="*", width=25)
    password_entry.grid(row=2, column=1, padx=10, pady=10)

    def login():
        """Handle login authentication"""
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter username and password")
            return

        user = database.authenticate_user(username, password)

        if user:
            messagebox.showinfo("Login Successful", f"Welcome {user['role']}!")
            on_login_success(user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    # Login button
    tk.Button(main_frame, text="Login", font=("Arial", 12, "bold"),
              bg="#d32f2f", fg="white", width=15,
              command=login).grid(row=3, column=0, columnspan=2, pady=20)

    # Bind Enter key
    password_entry.bind('<Return>', lambda event: login())


def clear_window(root):
    """Clear all widgets from window"""
    for widget in root.winfo_children():
        widget.destroy()