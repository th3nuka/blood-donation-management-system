import tkinter as tk
import database
import login
import dashboard
import donors
import inventory
import donations
import requests
import daily_report
import staff

# Global variables
current_user = None
root = None

def init_app():
    """Initialize the application"""
    global root

    # Create main window
    root = tk.Tk()
    root.title("Blood Donation Management System")
    root.geometry("1200x700")

    # Connect to database
    if not database.connect_db():
        print("Failed to connect to database. Please check your connection.")
        return

    # ✅ FIX ADDED HERE: Update database structure for enhanced donor fields
    database.update_existing_donors()

    # Start with login
    show_login()

    # Start main loop
    root.mainloop()

    # Close database connection when app exits
    database.close_db()

def show_login():
    """Show login window"""
    global current_user
    current_user = None
    login.create_login_window(root, on_login_success)

def on_login_success(user):
    """Handle successful login"""
    global current_user
    current_user = user
    print(f"DEBUG: Login successful, user: {user}")
    print(f"DEBUG: User role from login: {user.get('role')}")
    show_dashboard()

def show_dashboard():
    """Show dashboard"""
    global current_user
    print(f"DEBUG: Showing dashboard for user: {current_user}")
    dashboard.create_dashboard(root, current_user, open_window)

def open_window(window_name):
    """Open different windows based on selection"""
    if window_name == 'login':
        show_login()
    elif window_name == 'dashboard':
        show_dashboard()
    elif window_name == 'donors':
        donors.create_donors_window(root, current_user, lambda: open_window('dashboard'))
    elif window_name == 'inventory':
        inventory.create_inventory_window(root, current_user, lambda: open_window('dashboard'))
    elif window_name == 'donations':
        donations.create_donations_window(root, current_user, lambda: open_window('dashboard'))
    elif window_name == 'requests':
        requests.create_requests_window(root, current_user, lambda: open_window('dashboard'))
    elif window_name == 'daily_report':
        daily_report.create_daily_report_window(root, current_user, lambda: open_window('dashboard'))
    elif window_name == 'staff':
        # REMOVED ADMIN CHECK - ALL USERS CAN ACCESS STAFF MANAGEMENT
        staff.create_staff_window(root, current_user, lambda: open_window('dashboard'))
    else:
        # Default fallback
        show_dashboard()

if __name__ == "__main__":
    init_app()