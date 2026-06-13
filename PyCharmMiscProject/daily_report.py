# file name: daily_report.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import database
from datetime import datetime, timedelta
import csv
import os


def create_daily_report_window(root, user, go_back):
    """Create daily report window"""
    clear_window(root)

    root.title("Blood Donation System - Daily Report")
    root.geometry("1200x750")

    # Main container
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Title with Back button
    title_frame = tk.Frame(main_frame, bg="#f0f0f0")
    title_frame.pack(fill=tk.X, pady=(0, 20))

    tk.Button(title_frame, text="← Back to Dashboard",
              font=("Arial", 10, "bold"), bg="#d32f2f", fg="white",
              width=20, command=go_back).pack(side=tk.LEFT)

    tk.Label(title_frame, text="📋 Daily Donation Report",
             font=("Arial", 24, "bold"), bg="#f0f0f0"
             ).pack(side=tk.LEFT, expand=True)

    # Date Selection Frame
    date_frame = tk.LabelFrame(main_frame, text="Select Report Date",
                               font=("Arial", 12, "bold"),
                               bg="#ffffff", padx=20, pady=20)
    date_frame.pack(fill=tk.X, pady=(0, 20))

    tk.Label(date_frame, text="Report Date:", font=("Arial", 11), bg="#ffffff"
             ).grid(row=0, column=0, padx=5, pady=10, sticky=tk.E)

    report_date = DateEntry(date_frame, width=12, font=("Arial", 10),
                            date_pattern='yyyy-mm-dd')
    report_date.set_date(datetime.now())
    report_date.grid(row=0, column=1, padx=5, pady=10)

    # Quick date buttons
    quick_date_frame = tk.Frame(date_frame, bg="#ffffff")
    quick_date_frame.grid(row=0, column=2, padx=20, pady=10)

    def set_today():
        report_date.set_date(datetime.now())

    def set_yesterday():
        yesterday = datetime.now() - timedelta(days=1)
        report_date.set_date(yesterday)

    tk.Button(quick_date_frame, text="Today", font=("Arial", 9),
              bg="#4CAF50", fg="white", command=set_today
              ).pack(side=tk.LEFT, padx=2)
    tk.Button(quick_date_frame, text="Yesterday", font=("Arial", 9),
              bg="#2196F3", fg="white", command=set_yesterday
              ).pack(side=tk.LEFT, padx=2)

    # Generate Report Button
    def generate_report():
        selected_date = report_date.get()

        try:
            datetime.strptime(selected_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Invalid Date", "Please select a valid date")
            return

        # Clear previous results
        for widget in result_frame.winfo_children():
            widget.destroy()

        show_daily_report(selected_date)

    tk.Button(date_frame, text="📊 Generate Report", font=("Arial", 11, "bold"),
              bg="#d32f2f", fg="white", width=20,
              command=generate_report).grid(row=0, column=3, padx=10, pady=10)

    # Results Frame (with scrollbar)
    result_frame = tk.Frame(main_frame, bg="#ffffff")
    result_frame.pack(fill=tk.BOTH, expand=True)

    # Control buttons frame
    control_frame = tk.Frame(main_frame, bg="#f0f0f0")
    control_frame.pack(fill=tk.X, pady=10)

    def export_to_csv():
        selected_date = report_date.get()
        if not selected_date:
            messagebox.showerror("Error", "Please generate a report first")
            return

        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_date = selected_date.replace("-", "")
            filename = f"daily_report_{safe_date}_{timestamp}.csv"

            # Get data for the report
            data = get_daily_report_data(selected_date)

            if not data or len(data['rows']) == 0:
                messagebox.showinfo("No Data", "No data to export for this date")
                return

            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write header
                writer.writerow(data['header'])

                # Write data rows
                writer.writerows(data['rows'])

            # Show success message
            file_path = os.path.abspath(filename)
            messagebox.showinfo("Export Successful",
                                f"Report exported successfully!\n\nFile: {filename}\nLocation: {os.path.dirname(file_path)}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")

    tk.Button(control_frame, text="📥 Export to CSV", font=("Arial", 10),
              bg="#2196F3", fg="white", command=export_to_csv
              ).pack(side=tk.LEFT, padx=5)

    tk.Button(control_frame, text="🖨️ Print Report", font=("Arial", 10),
              bg="#9C27B0", fg="white",
              command=lambda: messagebox.showinfo("Print", "Print feature would be implemented here")
              ).pack(side=tk.LEFT, padx=5)

    tk.Button(control_frame, text="🔄 Refresh", font=("Arial", 10),
              bg="#FF9800", fg="white", command=generate_report
              ).pack(side=tk.LEFT, padx=5)

    tk.Button(control_frame, text="🏠 Back to Dashboard", font=("Arial", 10),
              bg="#d32f2f", fg="white", command=go_back
              ).pack(side=tk.RIGHT)

    def get_daily_report_data(selected_date):
        """Get daily report data for CSV export"""
        try:
            # Get donors who donated on selected date
            query = """
                SELECT d.donor_id, d.full_name, d.blood_type, d.contact, d.weight
                FROM donors d 
                WHERE d.last_donation_date = %s
                ORDER BY d.donor_id
            """
            donations = database.execute_query(query, (selected_date,), fetch=True)

            # Get blood inventory summary for the date
            inventory_query = "SELECT blood_type, units FROM inventory ORDER BY blood_type"
            inventory = database.execute_query(inventory_query, fetch=True)

            # Get statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_donations,
                    COUNT(DISTINCT d.donor_id) as unique_donors
                FROM donors d 
                WHERE d.last_donation_date = %s
            """
            stats = database.execute_query(stats_query, (selected_date,), fetchone=True)

            # Prepare CSV data
            header = ['Donor ID', 'Name', 'Blood Type', 'Contact', 'Weight (kg)', 'Donation Date']
            rows = []

            for donation in donations:
                rows.append([
                    donation['donor_id'],
                    donation['full_name'],
                    donation['blood_type'],
                    donation['contact'] or 'N/A',
                    donation['weight'] or 'N/A',
                    selected_date
                ])

            # Add summary section
            rows.append(['', '', '', '', '', ''])
            rows.append(['REPORT SUMMARY', '', '', '', '', ''])
            rows.append(['Total Donations', stats['total_donations'] if stats else 0, '', '', '', selected_date])
            rows.append(['Unique Donors', stats['unique_donors'] if stats else 0, '', '', '', selected_date])
            rows.append(['', '', '', '', '', ''])
            rows.append(['BLOOD INVENTORY SUMMARY', '', '', '', '', ''])

            if inventory:
                for item in inventory:
                    rows.append([f"  {item['blood_type']}", item['units'], '', '', '', selected_date])

            rows.append(['', '', '', '', '', ''])
            rows.append(['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '', '', '', ''])
            rows.append(['Generated By', user.get('username', 'System'), '', '', '', ''])

            return {'header': header, 'rows': rows}

        except Exception as e:
            print(f"Error getting report data: {e}")
            return None

    def show_daily_report(selected_date):
        """Display daily report with all details"""
        try:
            # Create main container with scrollbar
            main_container = tk.Frame(result_frame, bg="#ffffff")
            main_container.pack(fill=tk.BOTH, expand=True)

            # Create canvas for scrolling
            canvas = tk.Canvas(main_container, bg="#ffffff", highlightthickness=0)
            scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#ffffff")

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Report title
            tk.Label(scrollable_frame,
                     text=f"📋 DAILY DONATION REPORT - {selected_date}",
                     font=("Arial", 18, "bold"),
                     bg="#ffffff", fg="#d32f2f"
                     ).pack(anchor=tk.W, pady=(20, 30), padx=20)

            # Get donors who donated on selected date
            query = """
                SELECT d.donor_id, d.full_name, d.blood_type, d.contact, d.weight, d.last_donation_date
                FROM donors d 
                WHERE d.last_donation_date = %s
                ORDER BY d.donor_id
            """
            donations = database.execute_query(query, (selected_date,), fetch=True)

            # Get blood inventory summary
            inventory_query = "SELECT blood_type, units FROM inventory ORDER BY blood_type"
            inventory = database.execute_query(inventory_query, fetch=True)

            # Get statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_donations,
                    COUNT(DISTINCT d.donor_id) as unique_donors
                FROM donors d 
                WHERE d.last_donation_date = %s
            """
            stats = database.execute_query(stats_query, (selected_date,), fetchone=True)

            # Summary Statistics Section
            tk.Label(scrollable_frame,
                     text="📊 DAILY STATISTICS",
                     font=("Arial", 14, "bold"),
                     bg="#ffffff"
                     ).pack(anchor=tk.W, pady=(0, 15), padx=20)

            # Statistics cards
            stat_frame = tk.Frame(scrollable_frame, bg="#ffffff")
            stat_frame.pack(fill=tk.X, padx=20, pady=(0, 30))

            total_donations = stats['total_donations'] if stats else 0
            unique_donors = stats['unique_donors'] if stats else 0

            stat_cards = [
                ("Total Donations", total_donations, "#4CAF50", "Donations recorded"),
                ("Unique Donors", unique_donors, "#2196F3", "Individual donors"),
                ("Donation Rate", f"{(unique_donors / total_donations * 100):.1f}%" if total_donations > 0 else "0%",
                 "#9C27B0", "Donors per donation"),
            ]

            for i, (label, value, color, subtext) in enumerate(stat_cards):
                card = tk.Frame(stat_frame, bg=color, relief=tk.RAISED, bd=2)
                card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")

                # Configure grid weights
                stat_frame.columnconfigure(i, weight=1)

                # Card content
                inner_frame = tk.Frame(card, bg=color, padx=10, pady=10)
                inner_frame.pack(fill=tk.BOTH, expand=True)

                # Value (large)
                tk.Label(inner_frame, text=str(value),
                         font=("Arial", 28, "bold"),
                         bg=color, fg="white"
                         ).pack(expand=True)

                # Main label
                tk.Label(inner_frame, text=label,
                         font=("Arial", 11, "bold"),
                         bg=color, fg="white"
                         ).pack()

                # Subtext
                tk.Label(inner_frame, text=subtext,
                         font=("Arial", 9),
                         bg=color, fg="white"
                         ).pack()

            # Donation Details Section
            tk.Label(scrollable_frame,
                     text="👥 DAILY DONATIONS DETAIL",
                     font=("Arial", 14, "bold"),
                     bg="#ffffff"
                     ).pack(anchor=tk.W, pady=(20, 15), padx=20)

            if donations and len(donations) > 0:
                # Create table for donations
                table_frame = tk.Frame(scrollable_frame, bg="#f5f5f5", relief=tk.GROOVE, bd=1)
                table_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

                # Table header
                header_frame = tk.Frame(table_frame, bg="#e0e0e0")
                header_frame.pack(fill=tk.X)

                headers = ["Donor ID", "Name", "Blood Type", "Contact", "Weight (kg)"]
                for i, header in enumerate(headers):
                    tk.Label(header_frame, text=header,
                             font=("Arial", 11, "bold"),
                             bg="#e0e0e0", width=15
                             ).grid(row=0, column=i, padx=1, pady=5, sticky="nsew")
                    header_frame.columnconfigure(i, weight=1)

                # Donation rows
                for row_idx, donation in enumerate(donations):
                    row_color = "#ffffff" if row_idx % 2 == 0 else "#f9f9f9"

                    row_frame = tk.Frame(table_frame, bg=row_color)
                    row_frame.pack(fill=tk.X)

                    # Donor ID
                    tk.Label(row_frame, text=str(donation['donor_id']),
                             font=("Arial", 10),
                             bg=row_color, width=15
                             ).grid(row=0, column=0, padx=1, pady=3, sticky="w")

                    # Name
                    tk.Label(row_frame, text=donation['full_name'],
                             font=("Arial", 10),
                             bg=row_color, width=15
                             ).grid(row=0, column=1, padx=1, pady=3)

                    # Blood Type
                    tk.Label(row_frame, text=donation['blood_type'],
                             font=("Arial", 10),
                             bg=row_color, width=15
                             ).grid(row=0, column=2, padx=1, pady=3)

                    # Contact
                    contact = donation['contact'] or "N/A"
                    tk.Label(row_frame, text=contact,
                             font=("Arial", 10),
                             bg=row_color, width=15
                             ).grid(row=0, column=3, padx=1, pady=3)

                    # Weight
                    weight = f"{donation['weight']} kg" if donation['weight'] else "N/A"
                    tk.Label(row_frame, text=weight,
                             font=("Arial", 10),
                             bg=row_color, width=15
                             ).grid(row=0, column=4, padx=1, pady=3)

                    # Configure row grid
                    for col in range(5):
                        row_frame.columnconfigure(col, weight=1)
            else:
                # No donations message
                no_data_frame = tk.Frame(scrollable_frame, bg="#fff3e0", relief=tk.RAISED, bd=1)
                no_data_frame.pack(fill=tk.X, padx=20, pady=20)

                tk.Label(no_data_frame,
                         text=f"No donations recorded on {selected_date}",
                         font=("Arial", 12),
                         bg="#fff3e0", fg="#5D4037"
                         ).pack(padx=20, pady=20)

            # Blood Inventory Summary Section
            tk.Label(scrollable_frame,
                     text="🩸 BLOOD INVENTORY SUMMARY",
                     font=("Arial", 14, "bold"),
                     bg="#ffffff"
                     ).pack(anchor=tk.W, pady=(20, 15), padx=20)

            if inventory:
                # Create inventory grid
                inv_frame = tk.Frame(scrollable_frame, bg="#ffffff")
                inv_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

                blood_types = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

                for i, bt in enumerate(blood_types):
                    # Find units for this blood type
                    units = 0
                    for item in inventory:
                        if item['blood_type'] == bt:
                            units = item['units']
                            break

                    # Determine color based on stock level
                    if units >= 10:
                        color = "#4CAF50"  # Green - Adequate
                        status = "✅ Adequate"
                    elif units >= 5:
                        color = "#FF9800"  # Orange - Low
                        status = "⚠️ Low"
                    else:
                        color = "#f44336"  # Red - Critical
                        status = "🔴 Critical"

                    # Create blood type card
                    card = tk.Frame(inv_frame, bg=color, relief=tk.RAISED, bd=2,
                                    width=120, height=100)
                    card.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="nsew")
                    card.grid_propagate(False)

                    # Card content
                    tk.Label(card, text=bt,
                             font=("Arial", 16, "bold"),
                             bg=color, fg="white"
                             ).pack(expand=True, pady=(10, 0))

                    tk.Label(card, text=f"{units} units",
                             font=("Arial", 12),
                             bg=color, fg="white"
                             ).pack()

                    tk.Label(card, text=status,
                             font=("Arial", 9),
                             bg=color, fg="white"
                             ).pack(pady=(0, 10))

                # Configure grid weights
                for i in range(4):
                    inv_frame.columnconfigure(i, weight=1)

            # Report Footer
            footer_frame = tk.Frame(scrollable_frame, bg="#e3f2fd", relief=tk.RAISED, bd=2)
            footer_frame.pack(fill=tk.X, padx=20, pady=20)

            footer_text = f"""
            📋 REPORT SUMMARY - {selected_date}

            • Date: {selected_date}
            • Total Donations: {total_donations}
            • Unique Donors: {unique_donors}
            • Report Generated: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
            • Generated By: {user.get('username', 'System')} ({user.get('role', 'User')})

            Note: This report includes all donations recorded on the selected date.
            """

            tk.Label(footer_frame, text=footer_text,
                     font=("Arial", 11),
                     bg="#e3f2fd", justify=tk.LEFT
                     ).pack(padx=15, pady=15)

            # Update canvas scrolling
            canvas.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        except Exception as e:
            tk.Label(result_frame,
                     text=f"Error generating report: {str(e)}",
                     font=("Arial", 12), fg="red", bg="#ffffff"
                     ).pack(pady=50)
            print(f"Report error: {e}")

    # Initially show today's report
    show_daily_report(report_date.get())


def clear_window(root):
    """Clear all widgets from window"""
    for widget in root.winfo_children():
        widget.destroy()