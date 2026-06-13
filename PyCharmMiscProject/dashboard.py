import tkinter as tk
from tkinter import messagebox
import database


def create_dashboard(root, user, open_window):
    """Create dashboard"""
    clear_window(root)

    root.title("Blood Donation System - Dashboard")
    root.geometry("1200x700")

    # Header
    header_frame = tk.Frame(root, bg="#d32f2f", height=80)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)

    # Title
    tk.Label(header_frame, text="Blood Donation Management System",
             font=("Arial", 24, "bold"), bg="#d32f2f", fg="white"
             ).pack(side=tk.LEFT, padx=20, pady=20)

    # User info
    user_role = user.get('role', 'Unknown')
    tk.Label(header_frame, text=f"User: {user.get('username', 'Unknown')} ({user_role})",
             font=("Arial", 12), bg="#d32f2f", fg="white"
             ).pack(side=tk.RIGHT, padx=20, pady=20)

    # Logout button
    tk.Button(header_frame, text="Logout", font=("Arial", 10),
              bg="#ffffff", fg="#d32f2f",
              command=lambda: open_window('login')).pack(side=tk.RIGHT, padx=10)

    # Main content
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Dashboard title
    tk.Label(main_frame, text="Dashboard", font=("Arial", 20, "bold"),
             bg="#f0f0f0").pack(pady=(0, 20))

    # Statistics frame
    create_stats_frame(main_frame)

    # Navigation buttons
    create_navigation_buttons(main_frame, open_window, user)


def create_stats_frame(parent):
    """Create statistics display frame"""
    stats_frame = tk.Frame(parent, bg="#ffffff", relief=tk.RAISED, bd=1)
    stats_frame.pack(fill=tk.X, pady=(0, 20))

    stats = database.get_dashboard_stats()

    # Define stats cards
    stats_cards = [
        ("Total Donors", stats['total_donors'], "#4CAF50"),
        ("Blood Units", stats['total_blood_units'], "#f44336"),
        ("Pending Requests", stats['pending_requests'], "#FF9800"),
        ("Today's Donations", stats['today_donations'], "#2196F3")
    ]

    for i, (label, value, color) in enumerate(stats_cards):
        card_frame = tk.Frame(stats_frame, bg=color, width=200, height=100)
        card_frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
        card_frame.pack_propagate(False)

        # Center value
        tk.Label(card_frame, text=str(value), font=("Arial", 24, "bold"),
                 bg=color, fg="white").pack(expand=True)

        # Label
        tk.Label(card_frame, text=label, font=("Arial", 10),
                 bg=color, fg="white").pack(pady=(0, 10))

        # Configure column weights
        stats_frame.columnconfigure(i, weight=1)


def create_navigation_buttons(parent, open_window, user):
    """Create navigation buttons with role-based access"""
    nav_frame = tk.Frame(parent, bg="#f0f0f0")
    nav_frame.pack(pady=20)

    # Get user role (case-insensitive check)
    user_role = str(user.get('role', '')).lower()
    is_admin = user_role == 'admin'

    print(f"DEBUG: User role from database: '{user.get('role')}'")
    print(f"DEBUG: User role (lowercase): '{user_role}'")
    print(f"DEBUG: Is admin? {is_admin}")

    # Basic buttons for all users
    buttons = [
        ("Manage Donors", "donors", "#d32f2f"),
        ("Donation History", "donations", "#1976D2"),
        ("Blood Inventory", "inventory", "#7B1FA2"),
        ("Blood Requests", "requests", "#00897B"),
        ("Daily Report", "daily_report", "#9C27B0"),
    ]

    # Add Staff Management button only for admin (case-insensitive check)
    if is_admin:
        buttons.append(("Manage Staff", "staff", "#388E3C"))
        print("DEBUG: Adding Manage Staff button for admin")

    # Configure grid for proper layout
    # We want 3 columns for the first row, and 2 or 3 columns for second row
    num_columns = 3
    for i in range(num_columns):
        nav_frame.columnconfigure(i, weight=1)

    # Place buttons in grid
    row = 0
    col = 0

    for i, (text, window, color) in enumerate(buttons):
        btn = tk.Button(nav_frame, text=text, font=("Arial", 11, "bold"),
                        bg=color, fg="white", width=18, height=2,
                        command=lambda w=window: open_window(w))

        # Calculate position - first row up to 3 buttons, then second row
        if i < 3:  # First 3 buttons in first row
            row = 0
            col = i
        else:  # Remaining buttons in second row
            row = 1
            col = i - 3
            # Center the buttons in second row
            if len(buttons) <= 5:  # Only 5 buttons total (no staff management)
                col = i - 3
            else:  # 6 buttons total (with staff management)
                col = i - 3

        btn.grid(row=row, column=col, padx=5, pady=10, sticky="nsew")

        # Configure row weights for spacing
        nav_frame.rowconfigure(row, weight=1)

    # Add admin indicator if user is admin
    if is_admin:
        admin_frame = tk.Frame(parent, bg="#e8f5e9", relief=tk.GROOVE, bd=1)
        admin_frame.pack(fill=tk.X, pady=10)

        admin_text = "👑 Administrator Privileges: You have access to Staff Management"
        tk.Label(admin_frame, text=admin_text,
                 font=("Arial", 10), bg="#e8f5e9", fg="#2E7D32"
                 ).pack(padx=10, pady=5)


def clear_window(root):
    """Clear all widgets from window"""
    for widget in root.winfo_children():
        widget.destroy()