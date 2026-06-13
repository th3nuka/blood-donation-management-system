import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import csv
import os
import mysql.connector
from mysql.connector import Error


# ==================== DATABASE FUNCTIONS ====================
class Database:
    def __init__(self):
        self.connection = None
        self.connect_db()

    def connect_db(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="THEnuka@2007",  # Change this if needed
                database="blood_donation_db"
            )
            print("Database connected successfully")
            return self.connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            # Try to create database if it doesn't exist
            try:
                temp_conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="THEnuka@2007"
                )
                cursor = temp_conn.cursor()
                cursor.execute("CREATE DATABASE IF NOT EXISTS blood_donation_db")
                cursor.close()
                temp_conn.close()

                # Reconnect with database
                self.connection = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="THEnuka@2007",
                    database="blood_donation_db"
                )
                print("Database created and connected successfully")
                self.create_tables()
                return self.connection
            except Error as e2:
                print(f"Failed to create database: {e2}")
                return None

    def get_connection(self):
        """Get database connection"""
        if self.connection is None or not self.connection.is_connected():
            return self.connect_db()
        return self.connection

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            cursor = self.connection.cursor()

            # Create donors table with registration_date
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS donors (
                    donor_id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    blood_type VARCHAR(5) NOT NULL,
                    contact VARCHAR(20),
                    weight DECIMAL(5,2),
                    last_donation_date DATE,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create inventory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    blood_type VARCHAR(5) PRIMARY KEY,
                    units INT DEFAULT 0
                )
            """)

            # Create blood_requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blood_requests (
                    request_id INT AUTO_INCREMENT PRIMARY KEY,
                    blood_type VARCHAR(5) NOT NULL,
                    units INT NOT NULL,
                    request_date DATE NOT NULL,
                    status VARCHAR(20) DEFAULT 'Pending'
                )
            """)

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    role VARCHAR(20) DEFAULT 'staff'
                )
            """)

            # Insert default user if not exists
            cursor.execute("""
                INSERT IGNORE INTO users (username, password, role) 
                VALUES ('admin', 'admin123', 'admin')
            """)

            # Initialize blood types in inventory
            blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            for bt in blood_types:
                cursor.execute("""
                    INSERT IGNORE INTO inventory (blood_type, units) 
                    VALUES (%s, 0)
                """, (bt,))

            self.connection.commit()
            cursor.close()
            print("Tables created successfully")

        except Error as e:
            print(f"Error creating tables: {e}")

    def execute_query(self, query, params=None, fetch=False, fetchone=False):
        """Execute SQL query"""
        conn = self.get_connection()
        if not conn:
            return None

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())

            if fetch:
                return cursor.fetchall()
            elif fetchone:
                return cursor.fetchone()
            else:
                conn.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    # Dashboard Statistics
    def get_dashboard_stats(self):
        """Get statistics for dashboard"""
        stats = {}

        # Total donors
        query = "SELECT COUNT(*) as total FROM donors"
        result = self.execute_query(query, fetchone=True)
        stats['total_donors'] = result['total'] if result else 0

        # Total blood units
        query = "SELECT SUM(units) as total FROM inventory"
        result = self.execute_query(query, fetchone=True)
        stats['total_blood_units'] = result['total'] if result else 0

        # Pending requests
        query = "SELECT COUNT(*) as total FROM blood_requests WHERE status = 'Pending'"
        result = self.execute_query(query, fetchone=True)
        stats['pending_requests'] = result['total'] if result else 0

        # Today's donations
        query = "SELECT COUNT(*) as total FROM donors WHERE last_donation_date = CURDATE()"
        result = self.execute_query(query, fetchone=True)
        stats['today_donations'] = result['total'] if result else 0

        return stats

    # Daily Report Functions
    def get_daily_statistics(self, report_date):
        """Get daily statistics for reports"""
        stats = {}

        # Convert string date to proper format
        date_str = report_date

        # 1. New donors registered on the specific date
        query = """
            SELECT COUNT(*) as count 
            FROM donors 
            WHERE DATE(registration_date) = %s
        """
        result = self.execute_query(query, (date_str,), fetchone=True)
        stats['new_donors'] = result['count'] if result else 0

        # 2. Daily donations (donations made on the specific date)
        query = """
            SELECT COUNT(*) as count 
            FROM donors 
            WHERE last_donation_date = %s
        """
        result = self.execute_query(query, (date_str,), fetchone=True)
        stats['daily_donations'] = result['count'] if result else 0

        # 3. Total donors (up to the specific date)
        query = """
            SELECT COUNT(*) as count 
            FROM donors 
            WHERE registration_date <= %s
        """
        result = self.execute_query(query, (date_str + " 23:59:59",), fetchone=True)
        stats['total_donors'] = result['count'] if result else 0

        # 4. Total blood units available
        query = "SELECT SUM(units) as total FROM inventory"
        result = self.execute_query(query, fetchone=True)
        stats['total_blood_units'] = result['total'] if result else 0

        # 5. Blood accepted/rejected for the day (from requests)
        query = """
            SELECT 
                SUM(CASE WHEN status = 'Approved' THEN units ELSE 0 END) as accepted,
                SUM(CASE WHEN status = 'Rejected' THEN units ELSE 0 END) as rejected
            FROM blood_requests 
            WHERE request_date = %s
        """
        result = self.execute_query(query, (date_str,), fetchone=True)
        stats['blood_accepted'] = result['accepted'] if result and result['accepted'] else 0
        stats['blood_rejected'] = result['rejected'] if result and result['rejected'] else 0

        # 6. Blood units by type
        query = "SELECT blood_type, units FROM inventory ORDER BY blood_type"
        result = self.execute_query(query, fetch=True)

        stats['blood_by_type'] = {}
        if result:
            for bt in result:
                stats['blood_by_type'][bt['blood_type']] = bt['units']

        # Add date to stats
        stats['report_date'] = report_date

        return stats

    # Donor Functions
    def get_all_donors(self):
        """Get all donors"""
        query = "SELECT * FROM donors ORDER BY donor_id DESC"
        return self.execute_query(query, fetch=True)

    def get_donation_history(self):
        """Get all donation history"""
        query = """
        SELECT d.donor_id, d.full_name, d.blood_type, d.contact, 
               d.last_donation_date, d.weight, d.registration_date
        FROM donors d 
        WHERE d.last_donation_date IS NOT NULL
        ORDER BY d.last_donation_date DESC
        """
        return self.execute_query(query, fetch=True)

    def add_donor(self, full_name, blood_type, contact, weight):
        """Add new donor"""
        query = """
        INSERT INTO donors (full_name, blood_type, contact, weight, registration_date) 
        VALUES (%s, %s, %s, %s, CURDATE())
        """
        return self.execute_query(query, (full_name, blood_type, contact, weight))

    # Inventory Functions
    def get_inventory(self):
        """Get all blood inventory"""
        query = "SELECT * FROM inventory ORDER BY blood_type"
        return self.execute_query(query, fetch=True)

    # Blood Request Functions
    def get_blood_requests(self):
        """Get all blood requests"""
        query = "SELECT * FROM blood_requests ORDER BY request_date DESC"
        return self.execute_query(query, fetch=True)

    def get_blood_units(self, blood_type):
        """Get specific blood type units"""
        query = "SELECT units FROM inventory WHERE blood_type = %s"
        result = self.execute_query(query, (blood_type,), fetchone=True)
        return result['units'] if result else 0


# ==================== REPORT WINDOW ====================
def create_reports_window(root, user, go_back):
    """Create reports window with enhanced daily statistics"""
    clear_window(root)

    # Create database instance
    db = Database()

    root.title("Blood Donation System - Reports")
    root.geometry("1100x750")

    # Main container
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Title with Back button
    title_frame = tk.Frame(main_frame, bg="#f0f0f0")
    title_frame.pack(fill=tk.X, pady=(0, 20))

    tk.Button(title_frame, text="← Back to Dashboard",
              font=("Arial", 10, "bold"), bg="#d32f2f", fg="white",
              width=20, command=go_back).pack(side=tk.LEFT)

    tk.Label(title_frame, text="📊 Reports & Analytics",
             font=("Arial", 24, "bold"), bg="#f0f0f0"
             ).pack(side=tk.LEFT, expand=True)

    # Report Type Selection
    report_frame = tk.LabelFrame(main_frame, text="Select Report Type",
                                 font=("Arial", 12, "bold"),
                                 bg="#ffffff", padx=20, pady=20)
    report_frame.pack(fill=tk.X, pady=(0, 20))

    report_type = tk.StringVar(value="daily_report")

    reports = [
        ("📅 Daily Summary Report", "daily_report"),
        ("💉 Donation Summary", "donation_summary"),
        ("🩸 Blood Inventory", "inventory_report"),
        ("👥 Donor Activity", "donor_activity"),
        ("🆘 Blood Requests", "request_report"),
    ]

    for i, (text, value) in enumerate(reports):
        tk.Radiobutton(report_frame, text=text, variable=report_type,
                       value=value, font=("Arial", 11), bg="#ffffff"
                       ).grid(row=i // 2, column=i % 2, sticky=tk.W, padx=20, pady=10)

    # Date Selection
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

    def set_week_ago():
        week_ago = datetime.now() - timedelta(days=7)
        report_date.set_date(week_ago)

    tk.Button(quick_date_frame, text="Today", font=("Arial", 9),
              bg="#4CAF50", fg="white", command=set_today
              ).pack(side=tk.LEFT, padx=2)
    tk.Button(quick_date_frame, text="Yesterday", font=("Arial", 9),
              bg="#2196F3", fg="white", command=set_yesterday
              ).pack(side=tk.LEFT, padx=2)
    tk.Button(quick_date_frame, text="Last Week", font=("Arial", 9),
              bg="#FF9800", fg="white", command=set_week_ago
              ).pack(side=tk.LEFT, padx=2)

    # Generate Report Button
    def generate_report():
        report_type_val = report_type.get()
        selected_date = report_date.get()

        # Validate date
        try:
            datetime.strptime(selected_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Invalid Date", "Please select a valid date")
            return

        # Clear previous results
        for widget in result_frame.winfo_children():
            widget.destroy()

        try:
            if report_type_val == "daily_report":
                show_daily_report(selected_date, db)
            elif report_type_val == "donation_summary":
                show_donation_summary(selected_date, db)
            elif report_type_val == "inventory_report":
                show_inventory_report(db)
            elif report_type_val == "donor_activity":
                show_donor_activity(selected_date, db)
            elif report_type_val == "request_report":
                show_request_report(selected_date, db)
        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate report: {str(e)}")

    tk.Button(main_frame, text="📊 Generate Report", font=("Arial", 12, "bold"),
              bg="#4CAF50", fg="white", width=20, height=2,
              command=generate_report).pack(pady=10)

    # Results Frame
    result_frame = tk.Frame(main_frame, bg="#ffffff", relief=tk.SUNKEN, bd=1)
    result_frame.pack(fill=tk.BOTH, expand=True)

    # Export Button Functions
    def export_to_csv():
        try:
            report_type_val = report_type.get()
            selected_date = report_date.get()

            if not selected_date:
                messagebox.showerror("Error", "Please select a date first")
                return

            # Get data based on report type
            data = get_report_data(report_type_val, selected_date, db)

            if not data or not data.get('rows'):
                messagebox.showinfo("No Data", "No data to export for this report")
                return

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_date = selected_date.replace("-", "")
            filename = f"blood_report_{report_type_val}_{safe_date}_{timestamp}.csv"

            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write header
                writer.writerow(data['header'])

                # Write data rows
                writer.writerows(data['rows'])

            # Show success message with file location
            file_path = os.path.abspath(filename)
            messagebox.showinfo("Export Successful",
                                f"Report exported successfully!\n\nFile: {filename}\nLocation: {os.path.dirname(file_path)}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")

    def get_report_data(report_type_val, selected_date, db):
        """Get data for CSV export"""
        if report_type_val == "daily_report":
            stats = db.get_daily_statistics(selected_date)

            header = ['Category', 'Value', 'Date']
            rows = [
                ['New Donors Registered', stats.get('new_donors', 0), selected_date],
                ['Daily Donations', stats.get('daily_donations', 0), selected_date],
                ['Total Donors', stats.get('total_donors', 0), selected_date],
                ['Total Blood Units', stats.get('total_blood_units', 0), selected_date],
                ['Blood Units Accepted', stats.get('blood_accepted', 0), selected_date],
                ['Blood Units Rejected', stats.get('blood_rejected', 0), selected_date],
                ['', '', ''],
                ['Blood Type Breakdown', '', ''],
            ]

            # Add blood type details
            blood_types = stats.get('blood_by_type', {})
            for bt in ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]:
                units = blood_types.get(bt, 0)
                rows.append([f'  {bt}', units, selected_date])

            return {'header': header, 'rows': rows}

        elif report_type_val == "inventory_report":
            inventory = db.get_inventory()

            header = ['Blood Type', 'Units Available', 'Status', 'Timestamp']
            rows = []
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for item in inventory:
                units = item['units']
                if units >= 10:
                    status = "Adequate"
                elif units >= 5:
                    status = "Low"
                else:
                    status = "Critical"

                rows.append([item['blood_type'], units, status, timestamp])

            return {'header': header, 'rows': rows}

        elif report_type_val == "donation_summary":
            donations = db.get_donation_history()

            header = ['Donor ID', 'Name', 'Blood Type', 'Last Donation', 'Weight', 'Registration Date']
            rows = []

            for donation in donations:
                rows.append([
                    donation.get('donor_id', ''),
                    donation.get('full_name', ''),
                    donation.get('blood_type', ''),
                    donation.get('last_donation_date', ''),
                    donation.get('weight', ''),
                    donation.get('registration_date', '')
                ])

            return {'header': header, 'rows': rows}

        return None

    def print_report():
        """Print the current report"""
        report_type_val = report_type.get()
        selected_date = report_date.get()

        messagebox.showinfo("Print Report",
                            f"Printing {report_type_val} report for {selected_date}\n\n"
                            "Note: This feature would connect to a printer in a production system.")

    # Control buttons frame
    control_frame = tk.Frame(main_frame, bg="#f0f0f0")
    control_frame.pack(fill=tk.X, pady=10)

    tk.Button(control_frame, text="📥 Export to CSV", font=("Arial", 10),
              bg="#2196F3", fg="white", command=export_to_csv
              ).pack(side=tk.LEFT, padx=5)

    tk.Button(control_frame, text="🖨️ Print Report", font=("Arial", 10),
              bg="#9C27B0", fg="white", command=print_report
              ).pack(side=tk.LEFT, padx=5)

    tk.Button(control_frame, text="🔄 Refresh", font=("Arial", 10),
              bg="#FF9800", fg="white", command=lambda: generate_report()
              ).pack(side=tk.LEFT, padx=5)

    tk.Button(control_frame, text="🏠 Back to Dashboard", font=("Arial", 10),
              bg="#d32f2f", fg="white", command=go_back
              ).pack(side=tk.RIGHT)

    # Initially show daily report
    show_daily_report(report_date.get(), db)

    # ==================== REPORT DISPLAY FUNCTIONS ====================
    def show_daily_report(selected_date, db):
        """Show comprehensive daily report"""
        try:
            stats = db.get_daily_statistics(selected_date)

            # Create main container with scrollbar
            main_container = tk.Frame(result_frame, bg="#ffffff")
            main_container.pack(fill=tk.BOTH, expand=True)

            # Create canvas and scrollbar
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
                     text=f"📅 DAILY SUMMARY REPORT - {selected_date}",
                     font=("Arial", 18, "bold"),
                     bg="#ffffff", fg="#d32f2f"
                     ).pack(anchor=tk.W, pady=(20, 30), padx=20)

            # Summary Statistics Section
            tk.Label(scrollable_frame,
                     text="📊 DAILY STATISTICS",
                     font=("Arial", 14, "bold"),
                     bg="#ffffff"
                     ).pack(anchor=tk.W, pady=(0, 15), padx=20)

            # Statistics cards in grid
            stat_frame = tk.Frame(scrollable_frame, bg="#ffffff")
            stat_frame.pack(fill=tk.X, padx=20, pady=(0, 30))

            stat_cards = [
                ("👤 New Donors", stats.get('new_donors', 0), "#4CAF50", "Registered today"),
                ("💉 Daily Donations", stats.get('daily_donations', 0), "#2196F3", "Donations today"),
                ("📈 Total Donors", stats.get('total_donors', 0), "#9C27B0", "Cumulative count"),
                ("🩸 Total Blood Units", stats.get('total_blood_units', 0), "#f44336", "Current inventory"),
                ("✅ Blood Accepted", stats.get('blood_accepted', 0), "#4CAF50", "Today's approved"),
                ("❌ Blood Rejected", stats.get('blood_rejected', 0), "#f44336", "Today's rejected"),
            ]

            # Display 3 cards per row
            for i, (label, value, color, subtext) in enumerate(stat_cards):
                row = i // 3
                col = i % 3

                card = tk.Frame(stat_frame, bg=color, relief=tk.RAISED, bd=2)
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

                # Configure grid weights
                stat_frame.columnconfigure(col, weight=1)
                if row == 0:
                    stat_frame.rowconfigure(row, weight=1)

                # Card content
                inner_frame = tk.Frame(card, bg=color, padx=10, pady=10)
                inner_frame.pack(fill=tk.BOTH, expand=True)

                # Value (large)
                tk.Label(inner_frame, text=str(value),
                         font=("Arial", 32, "bold"),
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

            # Blood Inventory Section
            tk.Label(scrollable_frame,
                     text="🩸 BLOOD INVENTORY STATUS",
                     font=("Arial", 14, "bold"),
                     bg="#ffffff"
                     ).pack(anchor=tk.W, pady=(20, 15), padx=20)

            # Blood type table
            table_frame = tk.Frame(scrollable_frame, bg="#f5f5f5", relief=tk.GROOVE, bd=1)
            table_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

            # Table header
            header_frame = tk.Frame(table_frame, bg="#e0e0e0")
            header_frame.pack(fill=tk.X)

            headers = ["Blood Type", "Units Available", "Status", "Alert Level"]
            for i, header in enumerate(headers):
                tk.Label(header_frame, text=header,
                         font=("Arial", 11, "bold"),
                         bg="#e0e0e0", width=15
                         ).grid(row=0, column=i, padx=1, pady=5, sticky="nsew")
                header_frame.columnconfigure(i, weight=1)

            # Blood type rows
            blood_types = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
            blood_data = stats.get('blood_by_type', {})

            for row_idx, bt in enumerate(blood_types):
                units = blood_data.get(bt, 0)

                # Determine status and color
                if units >= 10:
                    status = "✅ Adequate"
                    alert = "🟢 Safe"
                    row_color = "#e8f5e8"
                elif units >= 5:
                    status = "⚠️ Low"
                    alert = "🟡 Warning"
                    row_color = "#fff3e0"
                else:
                    status = "🔴 Critical"
                    alert = "🔴 Critical"
                    row_color = "#ffebee"

                row_frame = tk.Frame(table_frame, bg=row_color)
                row_frame.pack(fill=tk.X)

                # Blood type
                tk.Label(row_frame, text=bt,
                         font=("Arial", 11, "bold"),
                         bg=row_color, width=15
                         ).grid(row=0, column=0, padx=1, pady=3, sticky="w")

                # Units
                tk.Label(row_frame, text=str(units),
                         font=("Arial", 11),
                         bg=row_color, width=15
                         ).grid(row=0, column=1, padx=1, pady=3)

                # Status
                tk.Label(row_frame, text=status,
                         font=("Arial", 10),
                         bg=row_color, width=15
                         ).grid(row=0, column=2, padx=1, pady=3)

                # Alert level
                tk.Label(row_frame, text=alert,
                         font=("Arial", 10),
                         bg=row_color, width=15
                         ).grid(row=0, column=3, padx=1, pady=3)

                # Configure row grid
                for col in range(4):
                    row_frame.columnconfigure(col, weight=1)

            # Summary Section
            summary_frame = tk.Frame(scrollable_frame, bg="#e3f2fd", relief=tk.RAISED, bd=2)
            summary_frame.pack(fill=tk.X, padx=20, pady=20)

            summary_text = f"""
            📋 REPORT SUMMARY - {selected_date}

            • New Registrations: {stats.get('new_donors', 0)} donor(s) registered today
            • Daily Donations: {stats.get('daily_donations', 0)} donation(s) recorded
            • Blood Processing: {stats.get('blood_accepted', 0)} unit(s) approved, {stats.get('blood_rejected', 0)} unit(s) rejected
            • Inventory Status: {stats.get('total_blood_units', 0)} total units across all blood types
            • Donor Base: {stats.get('total_donors', 0)} registered donors total

            Report generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}
            Generated by: {user.get('username', 'System')} ({user.get('role', 'User')})
            """

            tk.Label(summary_frame, text=summary_text,
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

    def show_donation_summary(selected_date, db):
        """Show donation summary report"""
        container = tk.Frame(result_frame, bg="#ffffff")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(container, text="💉 DONATION SUMMARY REPORT",
                 font=("Arial", 18, "bold"), bg="#ffffff"
                 ).pack(anchor=tk.W, pady=(0, 20))

        donations = db.get_donation_history()
        total_donations = len(donations) if donations else 0

        if not donations:
            tk.Label(container, text="No donation records found",
                     font=("Arial", 12), bg="#ffffff", fg="gray"
                     ).pack(pady=50)
            return

        # Summary stats
        stats_frame = tk.Frame(container, bg="#f0f0f0", relief=tk.RAISED, bd=1)
        stats_frame.pack(fill=tk.X, pady=(0, 20))

        # Count by blood type
        blood_type_counts = {}
        for donation in donations:
            bt = donation.get('blood_type', 'Unknown')
            blood_type_counts[bt] = blood_type_counts.get(bt, 0) + 1

        most_common = max(blood_type_counts.items(), key=lambda x: x[1]) if blood_type_counts else ('None', 0)

        summary_text = f"""
        Report Date: {selected_date}

        📈 Total Donations: {total_donations}
        🏆 Most Active Blood Type: {most_common[0]} ({most_common[1]} donations)

        🔢 Distribution by Blood Type:
        """

        for bt, count in sorted(blood_type_counts.items()):
            percentage = (count / total_donations * 100) if total_donations > 0 else 0
            summary_text += f"\n    • {bt}: {count} donations ({percentage:.1f}%)"

        summary_text += f"\n\n📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        tk.Label(stats_frame, text=summary_text,
                 font=("Arial", 11), bg="#f0f0f0", justify=tk.LEFT
                 ).pack(padx=15, pady=15)

        # Recent donations table
        tk.Label(container, text="📋 Recent Donations",
                 font=("Arial", 14, "bold"), bg="#ffffff"
                 ).pack(anchor=tk.W, pady=(20, 10))

        # Create table frame
        table_container = tk.Frame(container, bg="white")
        table_container.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ("Donor ID", "Name", "Blood Type", "Last Donation", "Weight")
        tree = ttk.Treeview(table_container, columns=columns, show="headings", height=8)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Add recent donations (last 10)
        recent_donations = donations[:10]
        for donation in recent_donations:
            tree.insert("", tk.END, values=(
                donation.get('donor_id', ''),
                donation.get('full_name', ''),
                donation.get('blood_type', ''),
                donation.get('last_donation_date', ''),
                f"{donation.get('weight', '')} kg" if donation.get('weight') else "N/A"
            ))

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show_inventory_report(db):
        """Show inventory report"""
        container = tk.Frame(result_frame, bg="#ffffff")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(container, text="🩸 BLOOD INVENTORY REPORT",
                 font=("Arial", 18, "bold"), bg="#ffffff"
                 ).pack(anchor=tk.W, pady=(0, 20))

        inventory = db.get_inventory()

        if not inventory:
            tk.Label(container, text="No inventory data available",
                     font=("Arial", 12), bg="#ffffff", fg="gray"
                     ).pack(pady=50)
            return

        # Total units
        total_units = sum(item['units'] for item in inventory)
        tk.Label(container,
                 text=f"Total Blood Units Available: {total_units}",
                 font=("Arial", 14, "bold"), bg="#ffffff", fg="#d32f2f"
                 ).pack(anchor=tk.W, pady=(0, 20))

        # Create visual inventory grid
        grid_frame = tk.Frame(container, bg="#ffffff")
        grid_frame.pack(fill=tk.BOTH, expand=True)

        blood_types = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

        for i, bt in enumerate(blood_types):
            # Find units for this blood type
            units = 0
            for item in inventory:
                if item['blood_type'] == bt:
                    units = item['units']
                    break

            # Determine color and status
            if units >= 10:
                color = "#4CAF50"  # Green
                status = "Adequate"
            elif units >= 5:
                color = "#FF9800"  # Orange
                status = "Low"
            else:
                color = "#f44336"  # Red
                status = "Critical"

            # Create blood type card
            card = tk.Frame(grid_frame, bg=color, relief=tk.RAISED, bd=3,
                            width=150, height=150)
            card.grid(row=i // 4, column=i % 4, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)

            # Card content
            inner_frame = tk.Frame(card, bg=color)
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Blood type
            tk.Label(inner_frame, text=bt,
                     font=("Arial", 24, "bold"),
                     bg=color, fg="white"
                     ).pack(expand=True)

            # Units
            tk.Label(inner_frame, text=f"{units} units",
                     font=("Arial", 16),
                     bg=color, fg="white"
                     ).pack()

            # Status
            tk.Label(inner_frame, text=status,
                     font=("Arial", 11),
                     bg=color, fg="white"
                     ).pack()

        # Configure grid weights
        for i in range(4):
            grid_frame.columnconfigure(i, weight=1)
        for i in range(2):
            grid_frame.rowconfigure(i, weight=1)

        # Status legend
        legend_frame = tk.Frame(container, bg="#f5f5f5", relief=tk.GROOVE, bd=1)
        legend_frame.pack(fill=tk.X, pady=20)

        legend_text = """
        📊 INVENTORY STATUS LEGEND:

        🟢 Adequate (10+ units): Stock is sufficient for normal operations
        🟡 Low (5-9 units): Stock is running low, consider scheduling donations
        🔴 Critical (0-4 units): Urgent need for donations of this blood type

        Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """

        tk.Label(legend_frame, text=legend_text,
                 font=("Arial", 10), bg="#f5f5f5", justify=tk.LEFT
                 ).pack(padx=10, pady=10)

    def show_donor_activity(selected_date, db):
        """Show donor activity report"""
        container = tk.Frame(result_frame, bg="#ffffff")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(container, text="👥 DONOR ACTIVITY REPORT",
                 font=("Arial", 18, "bold"), bg="#ffffff"
                 ).pack(anchor=tk.W, pady=(0, 20))

        donors = db.get_all_donors()

        if not donors:
            tk.Label(container, text="No donor data available",
                     font=("Arial", 12), bg="#ffffff", fg="gray"
                     ).pack(pady=50)
            return

        # Calculate statistics
        total_donors = len(donors)
        active_donors = len([d for d in donors if d.get('last_donation_date')])
        inactive_donors = total_donors - active_donors
        activity_rate = (active_donors / total_donors * 100) if total_donors > 0 else 0

        # New donors this month
        current_month = datetime.now().strftime('%Y-%m')
        new_this_month = len([d for d in donors
                              if d.get('registration_date')
                              and str(d['registration_date']).startswith(current_month)])

        # Statistics cards
        stats_frame = tk.Frame(container, bg="#ffffff")
        stats_frame.pack(fill=tk.X, pady=(0, 20))

        stat_cards = [
            ("Total Donors", total_donors, "#9C27B0"),
            ("Active Donors", active_donors, "#4CAF50"),
            ("Inactive Donors", inactive_donors, "#757575"),
            ("Activity Rate", f"{activity_rate:.1f}%", "#2196F3"),
            ("New This Month", new_this_month, "#FF9800"),
        ]

        for i, (label, value, color) in enumerate(stat_cards):
            card = tk.Frame(stats_frame, bg=color, relief=tk.RAISED, bd=2,
                            width=180, height=100)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            card.grid_propagate(False)

            tk.Label(card, text=str(value), font=("Arial", 24, "bold"),
                     bg=color, fg="white").pack(expand=True)
            tk.Label(card, text=label, font=("Arial", 10),
                     bg=color, fg="white").pack(pady=(0, 10))

            stats_frame.columnconfigure(i, weight=1)

        # Activity analysis
        analysis_frame = tk.Frame(container, bg="#f0f0f0", relief=tk.GROOVE, bd=1)
        analysis_frame.pack(fill=tk.X, pady=20)

        analysis_text = f"""
        📈 DONOR ACTIVITY ANALYSIS - {selected_date}

        • Total Donor Base: {total_donors} registered donors
        • Active Donors: {active_donors} ({activity_rate:.1f}% activity rate)
        • Inactive Donors: {inactive_donors} ({100 - activity_rate:.1f}% of total)
        • New Registrations This Month: {new_this_month} donors

        🎯 RECOMMENDATIONS:
        """

        if activity_rate < 30:
            analysis_text += "\n    ⚠️ Activity rate is low. Consider running donor engagement campaigns."
        elif activity_rate < 60:
            analysis_text += "\n    ⚠️ Moderate activity. Schedule reminder communications."
        else:
            analysis_text += "\n    ✅ Good activity rate. Maintain current engagement strategies."

        if new_this_month < 5:
            analysis_text += "\n    ⚠️ Low new registrations. Consider promoting donor registration."

        analysis_text += f"\n\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        tk.Label(analysis_frame, text=analysis_text,
                 font=("Arial", 11), bg="#f0f0f0", justify=tk.LEFT
                 ).pack(padx=15, pady=15)

        # Top donors table
        tk.Label(container, text="🏆 Top Active Donors",
                 font=("Arial", 14, "bold"), bg="#ffffff"
                 ).pack(anchor=tk.W, pady=(20, 10))

        # Sort donors by last donation date (most recent first)
        sorted_donors = sorted([d for d in donors if d.get('last_donation_date')],
                               key=lambda x: x['last_donation_date'],
                               reverse=True)[:10]

        if sorted_donors:
            table_frame = tk.Frame(container, bg="white")
            table_frame.pack(fill=tk.BOTH, expand=True)

            columns = ("Name", "Blood Type", "Last Donation", "Contact")
            tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=6)

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120)

            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            for donor in sorted_donors:
                tree.insert("", tk.END, values=(
                    donor.get('full_name', ''),
                    donor.get('blood_type', ''),
                    donor.get('last_donation_date', ''),
                    donor.get('contact', 'N/A')
                ))

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            tk.Label(container, text="No active donors found",
                     font=("Arial", 11), bg="#ffffff", fg="gray"
                     ).pack(pady=20)

    def show_request_report(selected_date, db):
        """Show blood request report"""
        container = tk.Frame(result_frame, bg="#ffffff")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(container, text="🆘 BLOOD REQUEST REPORT",
                 font=("Arial", 18, "bold"), bg="#ffffff"
                 ).pack(anchor=tk.W, pady=(0, 20))

        requests = db.get_blood_requests()

        if not requests:
            tk.Label(container, text="No request data available",
                     font=("Arial", 12), bg="#ffffff", fg="gray"
                     ).pack(pady=50)
            return

        # Calculate statistics
        total = len(requests)
        approved = len([r for r in requests if r['status'] == 'Approved'])
        pending = len([r for r in requests if r['status'] == 'Pending'])
        rejected = len([r for r in requests if r['status'] == 'Rejected'])

        # Calculate percentages safely
        approved_pct = (approved / total * 100) if total > 0 else 0
        pending_pct = (pending / total * 100) if total > 0 else 0
        rejected_pct = (rejected / total * 100) if total > 0 else 0

        # Statistics cards
        stats_frame = tk.Frame(container, bg="#ffffff")
        stats_frame.pack(fill=tk.X, pady=(0, 20))

        stat_cards = [
            ("Total Requests", total, "#9C27B0"),
            ("Approved", f"{approved}\n({approved_pct:.1f}%)", "#4CAF50"),
            ("Pending", f"{pending}\n({pending_pct:.1f}%)", "#FF9800"),
            ("Rejected", f"{rejected}\n({rejected_pct:.1f}%)", "#f44336"),
        ]

        for i, (label, value, color) in enumerate(stat_cards):
            card = tk.Frame(stats_frame, bg=color, relief=tk.RAISED, bd=2,
                            width=180, height=100)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            card.grid_propagate(False)

            tk.Label(card, text=str(value), font=("Arial", 20),
                     bg=color, fg="white").pack(expand=True)
            tk.Label(card, text=label, font=("Arial", 10),
                     bg=color, fg="white").pack(pady=(0, 10))

            stats_frame.columnconfigure(i, weight=1)

        # Request analysis
        analysis_frame = tk.Frame(container, bg="#f0f0f0", relief=tk.GROOVE, bd=1)
        analysis_frame.pack(fill=tk.X, pady=20)

        analysis_text = f"""
        📊 REQUEST ANALYSIS - {selected_date}

        • Total Requests Processed: {total}
        • Approval Rate: {approved_pct:.1f}% ({approved} approved)
        • Pending Requests: {pending} ({pending_pct:.1f}%)
        • Rejection Rate: {rejected_pct:.1f}% ({rejected} rejected)

        📅 Request Status Summary:
        """

        # Add status breakdown
        if approved_pct > 80:
            analysis_text += "\n    ✅ Excellent approval rate. Inventory management is effective."
        elif approved_pct > 60:
            analysis_text += "\n    ⚠️ Moderate approval rate. Review inventory levels."
        else:
            analysis_text += "\n    🔴 Low approval rate. Urgent need to increase blood stock."

        if pending > 5:
            analysis_text += f"\n    ⚠️ {pending} pending requests need attention."

        analysis_text += f"\n\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        tk.Label(analysis_frame, text=analysis_text,
                 font=("Arial", 11), bg="#f0f0f0", justify=tk.LEFT
                 ).pack(padx=15, pady=15)

        # Recent requests table
        tk.Label(container, text="📋 Recent Blood Requests",
                 font=("Arial", 14, "bold"), bg="#ffffff"
                 ).pack(anchor=tk.W, pady=(20, 10))

        # Create table
        table_frame = tk.Frame(container, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Request ID", "Blood Type", "Units", "Date", "Status")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

        col_widths = [100, 100, 80, 100, 100]
        for col, width in zip(columns, col_widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Color code rows based on status
        def set_row_color(status):
            if status == 'Approved':
                return '#e8f5e8'  # Light green
            elif status == 'Pending':
                return '#fff3e0'  # Light orange
            else:
                return '#ffebee'  # Light red

        # Add recent requests (last 15)
        recent_requests = requests[:15]
        for req in recent_requests:
            tree.insert("", tk.END, values=(
                req.get('request_id', ''),
                req.get('blood_type', ''),
                req.get('units', ''),
                req.get('request_date', ''),
                req.get('status', '')
            ))

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


def clear_window(root):
    """Clear all widgets from window"""
    for widget in root.winfo_children():
        widget.destroy()