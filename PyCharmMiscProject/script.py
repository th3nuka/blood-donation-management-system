import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from datetime import datetime, date
import re
import mysql.connector
from mysql.connector import Error


# ==================== DATABASE FUNCTIONS ====================
def create_connection():
    """Create database connection"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",  # CHANGE THIS
            password="THEnuka@2007",  # CHANGE THIS
        )

        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS blood_donation_db")
            cursor.execute("USE blood_donation_db")

            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS donors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    donor_id VARCHAR(10) UNIQUE,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    blood_type VARCHAR(5) NOT NULL,
                    contact VARCHAR(15) NOT NULL,
                    last_donation DATE NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    blood_type VARCHAR(5) PRIMARY KEY,
                    quantity INT DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    request_id VARCHAR(10) UNIQUE,
                    patient_name VARCHAR(100) NOT NULL,
                    blood_type VARCHAR(5) NOT NULL,
                    units_needed INT NOT NULL,
                    hospital VARCHAR(100) NOT NULL,
                    status VARCHAR(20) DEFAULT 'Pending',
                    request_date DATE NOT NULL
                )
            """)

            # Initialize inventory
            blood_types = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
            for bt in blood_types:
                cursor.execute("INSERT IGNORE INTO inventory VALUES (%s, 0)", (bt,))

            conn.commit()
            cursor.close()

            # Reconnect to the created database
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="blood_donation_db"
            )
            return conn

    except Error as e:
        print(f"Database Error: {e}")
        return None


# Global database connection
conn = create_connection()


def get_donors():
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM donors ORDER BY last_donation DESC")
        donors = cursor.fetchall()
        cursor.close()
        return donors
    except Error as e:
        print(f"Error: {e}")
        return []


def add_donor(donor_id, first_name, last_name, blood_type, contact, last_donation):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO donors (donor_id, first_name, last_name, blood_type, contact, last_donation)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (donor_id, first_name, last_name, blood_type, contact, last_donation))
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False


def get_inventory():
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM inventory")
        items = cursor.fetchall()
        cursor.close()

        inventory_dict = {}
        for item in items:
            inventory_dict[item['blood_type']] = item['quantity']
        return inventory_dict
    except Error as e:
        print(f"Error: {e}")
        return {}


def update_inventory(blood_type, quantity_change):
    try:
        cursor = conn.cursor()
        # Get current quantity
        cursor.execute("SELECT quantity FROM inventory WHERE blood_type = %s", (blood_type,))
        result = cursor.fetchone()

        if result:
            current = result[0]
            new_quantity = current + quantity_change
            if new_quantity < 0:
                new_quantity = 0

            cursor.execute("UPDATE inventory SET quantity = %s WHERE blood_type = %s",
                           (new_quantity, blood_type))
            conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False


def get_requests():
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM requests ORDER BY request_date DESC")
        requests = cursor.fetchall()
        cursor.close()
        return requests
    except Error as e:
        print(f"Error: {e}")
        return []


def add_request(request_id, patient_name, blood_type, units_needed, hospital, request_date):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO requests (request_id, patient_name, blood_type, units_needed, hospital, request_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (request_id, patient_name, blood_type, units_needed, hospital, request_date))
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False


def update_request_status(request_id, status):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE requests SET status = %s WHERE request_id = %s",
                       (status, request_id))
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False


# ==================== UI HELPER FUNCTIONS ====================
def clear_container(container):
    for widget in container.winfo_children():
        widget.destroy()


# ==================== LOGIN PAGE ====================
def show_login_page(root):
    clear_container(root)

    # Background
    try:
        bg_img = Image.open("bg.jpg").resize((1100, 700), Image.LANCZOS)
        root.bg_photo = ImageTk.PhotoImage(bg_img)
        tk.Label(root, image=root.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)
    except:
        root.configure(bg="white")

    # Login frame
    frame = tk.Frame(root, bg="white", padx=40, pady=40)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(frame, text="Blood Donation System",
             font=("Arial", 24, "bold"), bg="white", fg="#8B0000").pack(pady=(0, 30))

    tk.Label(frame, text="Username", font=("Arial", 12), bg="white").pack(anchor="w", pady=(0, 5))
    user_entry = tk.Entry(frame, font=("Arial", 12), width=25)
    user_entry.pack(pady=(0, 15))
    user_entry.focus_set()

    tk.Label(frame, text="Password", font=("Arial", 12), bg="white").pack(anchor="w", pady=(0, 5))
    pass_entry = tk.Entry(frame, font=("Arial", 12), width=25, show="*")
    pass_entry.pack(pady=(0, 20))

    def login():
        if user_entry.get() == "admin" and pass_entry.get() == "admin1234":
            show_main_app(root)
        else:
            messagebox.showerror("Error", "Invalid credentials")

    tk.Button(frame, text="Login", font=("Arial", 12),
              bg="#8B0000", fg="white", width=15, command=login).pack()

    root.bind('<Return>', lambda e: login())


# ==================== MAIN APPLICATION LAYOUT ====================
def show_main_app(root):
    clear_container(root)
    root.unbind('<Return>')

    # Header
    header = tk.Frame(root, bg="#8B0000", height=60)
    header.pack(side="top", fill="x")
    tk.Label(header, text="Blood Donation System",
             font=("Arial", 18, "bold"), bg="#8B0000", fg="white").pack(pady=15)

    # Main container
    main_container = tk.Frame(root, bg="#f0f0f0")
    main_container.pack(fill="both", expand=True)

    # Sidebar
    sidebar = tk.Frame(main_container, bg="#e8e8e8", width=180)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="Menu", font=("Arial", 12, "bold"),
             bg="#e8e8e8", pady=15).pack()

    # Content area
    content_area = tk.Frame(main_container, bg="white")
    content_area.pack(side="right", fill="both", expand=True, padx=15, pady=15)

    # Menu buttons
    def create_btn(text, command):
        btn = tk.Button(sidebar, text=text, anchor="w", padx=20, pady=12,
                        relief="flat", bg="#e8e8e8", font=("Arial", 10),
                        command=command)
        btn.pack(fill="x", pady=1)
        return btn

    create_btn("Dashboard", lambda: show_dashboard(content_area))
    create_btn("Donors", lambda: show_donors(content_area))
    create_btn("Inventory", lambda: show_inventory(content_area))
    create_btn("Requests", lambda: show_requests(content_area))
    tk.Frame(sidebar, height=2, bg="#cccccc").pack(fill="x", pady=10)
    create_btn("Logout", lambda: show_login_page(root))

    # Show dashboard by default
    show_dashboard(content_area)


# ==================== DASHBOARD PAGE ====================
def show_dashboard(container):
    clear_container(container)

    donors = get_donors()
    inventory = get_inventory()
    requests = get_requests()

    donor_count = len(donors)
    total_units = sum(inventory.values())
    pending_requests = len([r for r in requests if r['status'] == 'Pending'])

    tk.Label(container, text="Dashboard", font=("Arial", 20, "bold"),
             bg="white").pack(anchor="w", pady=10)

    # Cards
    frame = tk.Frame(container, bg="white")
    frame.pack(fill="x", pady=20)

    def create_card(title, value, col):
        card = tk.Frame(frame, bg="#f5f5f5", width=180, height=100,
                        highlightthickness=1, highlightbackground="#cccccc")
        card.grid(row=0, column=col, padx=10)
        card.grid_propagate(False)
        tk.Label(card, text=title, bg="#f5f5f5").pack(pady=(20, 5))
        tk.Label(card, text=str(value), font=("Arial", 24, "bold"), bg="#f5f5f5").pack()
        return card

    create_card("Total Donors", donor_count, 0)
    create_card("Blood Units", total_units, 1)
    create_card("Pending Requests", pending_requests, 2)

    # Recent donors
    tk.Label(container, text="Recent Donors", font=("Arial", 14, "bold"),
             bg="white").pack(anchor="w", pady=(20, 10))

    if donors:
        cols = ("ID", "Name", "Blood Type", "Last Donation")
        tree = ttk.Treeview(container, columns=cols, show="headings", height=5)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        for d in donors[:5]:
            tree.insert("", "end", values=(
                d["donor_id"],
                f"{d['first_name']} {d['last_name']}",
                d["blood_type"],
                d["last_donation"]
            ))
        tree.pack(fill="both", expand=True, pady=(0, 20))
    else:
        tk.Label(container, text="No donors yet", bg="white", fg="gray").pack(pady=50)


# ==================== DONORS PAGE ====================
def show_donors(container):
    clear_container(container)

    tk.Label(container, text="Donor Records", font=("Arial", 20, "bold"),
             bg="white").pack(anchor="w", pady=10)

    # Search
    search_frame = tk.Frame(container, bg="white")
    search_frame.pack(fill="x", pady=(0, 10))
    tk.Label(search_frame, text="Search:", bg="white").pack(side="left", padx=(0, 5))
    search_entry = tk.Entry(search_frame, width=25)
    search_entry.pack(side="left")

    # Treeview
    tree_frame = tk.Frame(container)
    tree_frame.pack(fill="both", expand=True, pady=10)

    cols = ("ID", "Name", "Blood Type", "Contact", "Last Donation")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
    for col in cols:
        tree.heading(col, text=col)
        if col == "Name":
            tree.column(col, width=150)
        else:
            tree.column(col, width=100)

    # Add donors
    donors = get_donors()
    for d in donors:
        tree.insert("", "end", values=(
            d["donor_id"],
            f"{d['first_name']} {d['last_name']}",
            d["blood_type"],
            d["contact"],
            d["last_donation"]
        ))

    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    # Add donor button
    tk.Button(container, text="Add New Donor", bg="#8B0000", fg="white",
              padx=15, pady=8, command=lambda: add_donor_window(container)).pack(pady=10)


def add_donor_window(parent_container):
    win = tk.Toplevel()
    win.title("Add Donor")
    win.geometry("400x500")
    win.configure(bg="white")

    tk.Label(win, text="Add New Donor", font=("Arial", 16)).pack(pady=20)

    frame = tk.Frame(win, bg="white", padx=20, pady=10)
    frame.pack(fill="both", expand=True)

    # Form fields
    fields = []
    labels = ["First Name:", "Last Name:", "Blood Type:", "Contact:", "Last Donation:", "Units:"]

    for i, label in enumerate(labels):
        tk.Label(frame, text=label, bg="white").pack(anchor="w", pady=(5, 0))
        if label == "Blood Type:":
            entry = ttk.Combobox(frame, values=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"],
                                 state="readonly", width=28)
            entry.set("Select")
        else:
            entry = tk.Entry(frame, width=30)
            if label == "Last Donation:":
                entry.insert(0, date.today().strftime("%Y-%m-%d"))
            elif label == "Units:":
                entry.insert(0, "1")

        entry.pack(pady=(0, 10))
        fields.append(entry)

    def save():
        values = [field.get().strip() for field in fields]

        # Validate
        if not all(values[:5]) or values[2] == "Select":
            messagebox.showerror("Error", "Please fill all fields")
            return

        # Generate ID
        donors = get_donors()
        new_id = f"D{len(donors) + 1:03d}"

        # Add donor
        if add_donor(new_id, values[0], values[1], values[2], values[3], values[4]):
            # Update inventory
            try:
                units = int(values[5])
                update_inventory(values[2], units)
                messagebox.showinfo("Success", "Donor added")
                win.destroy()
                show_donors(parent_container)
            except:
                messagebox.showerror("Error", "Invalid units")
        else:
            messagebox.showerror("Error", "Failed to add donor")

    # Buttons
    btn_frame = tk.Frame(frame, bg="white")
    btn_frame.pack(fill="x", pady=10)
    tk.Button(btn_frame, text="Cancel", bg="#999999", fg="white",
              padx=15, pady=5, command=win.destroy).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Save", bg="#8B0000", fg="white",
              padx=15, pady=5, command=save).pack(side="right", padx=5)


# ==================== INVENTORY PAGE ====================
def show_inventory(container):
    clear_container(container)

    inventory = get_inventory()

    tk.Label(container, text="Blood Inventory", font=("Arial", 20, "bold"),
             bg="white").pack(anchor="w", pady=10)

    total = sum(inventory.values())
    tk.Label(container, text=f"Total Units: {total}",
             font=("Arial", 12), bg="white").pack(anchor="w", pady=(0, 20))

    # Blood type grid
    frame = tk.Frame(container, bg="white")
    frame.pack(fill="both", expand=True)

    row, col = 0, 0
    for blood_type in ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]:
        count = inventory.get(blood_type, 0)

        if count == 0:
            color = "#ffcccc"
        elif count < 5:
            color = "#ffcc99"
        else:
            color = "#ccffcc"

        btn = tk.Button(frame, text=f"{blood_type}\n{count} units",
                        bg=color, width=10, height=4)
        btn.grid(row=row, column=col, padx=10, pady=10)

        col += 1
        if col > 3:
            col = 0
            row += 1


# ==================== REQUESTS PAGE ====================
def show_requests(container):
    clear_container(container)

    requests = get_requests()
    inventory = get_inventory()

    tk.Label(container, text="Blood Requests", font=("Arial", 20, "bold"),
             bg="white").pack(anchor="w", pady=10)

    # Add button
    tk.Button(container, text="Add New Request", bg="#8B0000", fg="white",
              padx=15, pady=8, command=lambda: add_request_window(container)).pack(anchor="e", pady=(0, 10))

    # Treeview
    tree_frame = tk.Frame(container)
    tree_frame.pack(fill="both", expand=True, pady=10)

    cols = ("Request ID", "Patient", "Blood Type", "Units", "Hospital", "Status", "Date")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    for req in requests:
        tree.insert("", "end", values=(
            req["request_id"],
            req["patient_name"],
            req["blood_type"],
            req["units_needed"],
            req["hospital"],
            req["status"],
            req["request_date"]
        ))

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    # Action buttons
    def approve():
        selected = tree.selection()
        if selected:
            req_id = tree.item(selected[0])['values'][0]
            if update_request_status(req_id, "Approved"):
                messagebox.showinfo("Success", "Request approved")
                show_requests(container)

    def reject():
        selected = tree.selection()
        if selected:
            req_id = tree.item(selected[0])['values'][0]
            if update_request_status(req_id, "Rejected"):
                messagebox.showinfo("Success", "Request rejected")
                show_requests(container)

    btn_frame = tk.Frame(container, bg="white")
    btn_frame.pack(fill="x", pady=10)
    tk.Button(btn_frame, text="Approve", bg="#4CAF50", fg="white",
              padx=10, pady=5, command=approve).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Reject", bg="#f44336", fg="white",
              padx=10, pady=5, command=reject).pack(side="left", padx=5)


def add_request_window(parent_container):
    win = tk.Toplevel()
    win.title("New Request")
    win.geometry("400x450")
    win.configure(bg="white")

    tk.Label(win, text="New Blood Request", font=("Arial", 16)).pack(pady=20)

    frame = tk.Frame(win, bg="white", padx=20, pady=10)
    frame.pack(fill="both", expand=True)

    # Form fields
    fields = []
    labels = ["Patient Name:", "Blood Type:", "Units Needed:", "Hospital:", "Request Date:"]

    for label in labels:
        tk.Label(frame, text=label, bg="white").pack(anchor="w", pady=(5, 0))
        if label == "Blood Type:":
            entry = ttk.Combobox(frame, values=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"],
                                 state="readonly", width=28)
            entry.set("Select")
        else:
            entry = tk.Entry(frame, width=30)
            if label == "Request Date:":
                entry.insert(0, date.today().strftime("%Y-%m-%d"))
            elif label == "Units Needed:":
                entry.insert(0, "1")

        entry.pack(pady=(0, 10))
        fields.append(entry)

    def submit():
        values = [field.get().strip() for field in fields]

        if not all(values) or values[1] == "Select":
            messagebox.showerror("Error", "Please fill all fields")
            return

        # Generate ID
        requests = get_requests()
        new_id = f"REQ{len(requests) + 1:03d}"

        if add_request(new_id, values[0], values[1], int(values[2]), values[3], values[4]):
            messagebox.showinfo("Success", "Request submitted")
            win.destroy()
            show_requests(parent_container)
        else:
            messagebox.showerror("Error", "Failed to submit")

    # Buttons
    btn_frame = tk.Frame(frame, bg="white")
    btn_frame.pack(fill="x", pady=10)
    tk.Button(btn_frame, text="Cancel", bg="#999999", fg="white",
              padx=15, pady=5, command=win.destroy).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Submit", bg="#8B0000", fg="white",
              padx=15, pady=5, command=submit).pack(side="right", padx=5)


# ==================== MAIN APPLICATION ====================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Blood Donation System")
    root.geometry("1100x700")

    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.minsize(1000, 600)

    # Check database
    if conn is None:
        messagebox.showerror("Database Error", "Cannot connect to MySQL")

    show_login_page(root)
    root.mainloop()

    if conn and conn.is_connected():
        conn.close()