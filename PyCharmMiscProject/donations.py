import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import database


def create_donations_window(root, user, go_back):
    """Create donations history window"""
    clear_window(root)

    root.title("Blood Donation System - Donation History")
    root.geometry("1000x600")  # Set a fixed size

    # Main container
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Title with Back button - TOP SECTION
    title_frame = tk.Frame(main_frame, bg="#f0f0f0")
    title_frame.pack(fill=tk.X, pady=(0, 20))

    # Back button on LEFT
    tk.Button(title_frame, text="← Back to Dashboard",
              font=("Arial", 10, "bold"), bg="#d32f2f", fg="white",
              width=20, command=go_back).pack(side=tk.LEFT)

    # Title in CENTER
    tk.Label(title_frame, text="Donation History",
             font=("Arial", 24, "bold"), bg="#f0f0f0"
             ).pack(side=tk.LEFT, expand=True)

    # Empty space on RIGHT
    tk.Label(title_frame, bg="#f0f0f0", width=20).pack(side=tk.RIGHT)

    # Status message
    status_label = tk.Label(main_frame, text="", font=("Arial", 11),
                            bg="#f0f0f0", fg="#d32f2f")
    status_label.pack(pady=(0, 10))

    # Table frame
    table_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, bd=1)
    table_frame.pack(fill=tk.BOTH, expand=True)

    # Create treeview
    columns = ("ID", "Donor Name", "Blood Type", "Contact", "Last Donation", "Weight")
    donations_tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", height=20)

    # Configure columns
    col_widths = [50, 200, 100, 150, 150, 80]
    for col, width in zip(columns, col_widths):
        donations_tree.heading(col, text=col)
        donations_tree.column(col, width=width, minwidth=width)

    # Scrollbars
    y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                command=donations_tree.yview)
    donations_tree.configure(yscrollcommand=y_scrollbar.set)
    y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL,
                                command=donations_tree.xview)
    donations_tree.configure(xscrollcommand=x_scrollbar.set)
    x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    donations_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def load_donations():
        """Load donations into treeview"""
        # Clear existing items
        for item in donations_tree.get_children():
            donations_tree.delete(item)

        # Clear any existing help text
        for widget in main_frame.winfo_children():
            if isinstance(widget, tk.Label) and "To add donations" in widget.cget("text"):
                widget.destroy()

        # Get donation history from database
        donations = database.get_donation_history()

        if donations and len(donations) > 0:
            for donation in donations:
                donations_tree.insert("", tk.END, values=(
                    donation['donor_id'],
                    donation['full_name'],
                    donation['blood_type'],
                    donation['contact'] or "No contact",
                    donation['last_donation_date'] or "No donation",
                    f"{donation['weight']} kg" if donation['weight'] else "N/A"
                ))

            # Update status
            total_donors = len(donations)
            status_label.config(text=f"✅ Showing {total_donors} donation records",
                                fg="#4CAF50")

        else:
            # Show help message
            status_label.config(text="⚠️ No donation records found", fg="#FF9800")

            help_frame = tk.Frame(main_frame, bg="#FFF3E0", relief=tk.RAISED, bd=1)
            help_frame.pack(fill=tk.X, pady=10)

            help_text = """To add donation records:
            1. Click 'Back to Dashboard'
            2. Go to 'Manage Donors'
            3. Select a donor
            4. Click 'Record Donation'
            5. Choose a donation date"""

            tk.Label(help_frame, text=help_text, font=("Arial", 10),
                     bg="#FFF3E0", fg="#5D4037", justify=tk.LEFT
                     ).pack(padx=20, pady=10)

            # Add sample data button
            def add_sample_data():
                add_sample_donations()
                load_donations()

            tk.Button(help_frame, text="Add Sample Donation Data",
                      font=("Arial", 10), bg="#4CAF50", fg="white",
                      command=add_sample_data).pack(pady=(0, 10))

    def add_sample_donations():
        """Add sample donation data for testing"""
        try:
            # First check if we have donors
            all_donors = database.get_all_donors()

            if not all_donors or len(all_donors) == 0:
                # Add sample donors first
                sample_donors = [
                    ("John Smith", "A+", "0771234567", 70.5),
                    ("Maria Garcia", "O-", "0772345678", 65.0),
                    ("David Lee", "B+", "0773456789", 80.0)
                ]

                for name, blood_type, contact, weight in sample_donors:
                    database.add_donor(name, blood_type, contact, weight)

                # Get the newly added donors
                all_donors = database.get_all_donors()

            # Record donations for some donors
            import datetime
            today = datetime.date.today()

            # Record donations for first 3 donors
            for i, donor in enumerate(all_donors[:3]):
                donation_date = today - datetime.timedelta(days=(i + 1) * 10)
                database.record_donation(donor['donor_id'], donation_date)

            messagebox.showinfo("Success", "Sample donation data added!")

        except Exception as e:
            messagebox.showerror("Error", f"Could not add sample data: {str(e)}")

    # Load data immediately
    load_donations()

    # Bottom buttons - BOTTOM SECTION
    bottom_frame = tk.Frame(main_frame, bg="#f0f0f0", pady=10)
    bottom_frame.pack(fill=tk.X)

    # Left side buttons
    left_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
    left_frame.pack(side=tk.LEFT)

    tk.Button(left_frame, text="🔄 Refresh", font=("Arial", 10),
              bg="#2196F3", fg="white", command=load_donations
              ).pack(side=tk.LEFT, padx=5)

    tk.Button(left_frame, text="📊 Statistics", font=("Arial", 10),
              bg="#9C27B0", fg="white",
              command=lambda: messagebox.showinfo("Statistics",
                                                  "Total donations will be shown here")
              ).pack(side=tk.LEFT, padx=5)

    # Right side - Back button
    tk.Button(bottom_frame, text="🏠 Back to Dashboard",
              font=("Arial", 10, "bold"), bg="#d32f2f", fg="white",
              command=go_back).pack(side=tk.RIGHT)

    # Center - Show total count
    total_count = len(donations_tree.get_children())
    count_label = tk.Label(bottom_frame,
                           text=f"Total Records: {total_count}",
                           font=("Arial", 10, "bold"),
                           bg="#f0f0f0", fg="#555555")
    count_label.pack(side=tk.LEFT, padx=20, expand=True)

    # Update count when treeview changes
    def update_count():
        count = len(donations_tree.get_children())
        count_label.config(text=f"Total Records: {count}")

    # Bind treeview update event
    donations_tree.bind('<<TreeviewSelect>>', lambda e: update_count())


def clear_window(root):
    """Clear all widgets from window"""
    for widget in root.winfo_children():
        widget.destroy()