import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Global database connection
connection = None


def connect_db():
    """Connect to MySQL database"""
    global connection
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="THEnuka@2007",
            database="blood_donation"
        )
        print("Database connected successfully")

        # Initialize database when connected
        initialize_database()

        return connection
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
            cursor.execute("CREATE DATABASE IF NOT EXISTS blood_donation")
            cursor.close()
            temp_conn.close()

            # Reconnect with database
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="THEnuka@2007",
                database="blood_donation_db"
            )
            print("Database created and connected successfully")

            # Initialize database
            initialize_database()

            return connection
        except Error as e2:
            print(f"Failed to create database: {e2}")
            return None


def get_connection():
    """Get database connection"""
    global connection
    if connection is None or not connection.is_connected():
        return connect_db()
    return connection


def close_db():
    """Close database connection"""
    global connection
    if connection and connection.is_connected():
        connection.close()
        print("Database connection closed")


def execute_query(query, params=None, fetch=False, fetchone=False):
    """Execute SQL query"""
    conn = get_connection()
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


def initialize_database():
    """Initialize database tables and default data"""
    try:
        # Create tables if they don't exist
        cursor = get_connection().cursor()

        # Create donors table with enhanced fields - FIXED: removed registration_date from initial create
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS donors (
                donor_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                blood_type VARCHAR(5) NOT NULL,
                contact VARCHAR(20),
                weight DECIMAL(5,2),
                height DECIMAL(5,2),
                address TEXT,
                gender VARCHAR(10),
                date_of_birth DATE,
                has_ncd BOOLEAN DEFAULT FALSE,
                last_donation_date DATE
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

        # Create donations_history table for tracking donations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS donations_history (
                donation_id INT AUTO_INCREMENT PRIMARY KEY,
                donor_id INT NOT NULL,
                donation_date DATE NOT NULL,
                units_collected INT DEFAULT 1,
                FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE
            )
        """)

        # Insert default admin user if not exists
        cursor.execute("""
            INSERT IGNORE INTO users (username, password, role) 
            VALUES ('admin', 'admin123', 'admin')
        """)

        # Make sure existing admin user has correct role
        cursor.execute("""
            UPDATE users SET role = 'admin' WHERE username = 'admin'
        """)

        # Initialize blood types in inventory
        blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for bt in blood_types:
            cursor.execute("""
                INSERT IGNORE INTO inventory (blood_type, units) 
                VALUES (%s, 0)
            """, (bt,))

        get_connection().commit()
        cursor.close()
        print("Database initialized successfully")

    except Error as e:
        print(f"Error initializing database: {e}")


# User Functions
def authenticate_user(username, password):
    """Authenticate user login"""
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    return execute_query(query, (username, password), fetchone=True)


# Donor Functions - ENHANCED VERSIONS
def get_all_donors():
    """Get all donors with all fields - FIXED: removed registration_date"""
    query = """
    SELECT donor_id, full_name, blood_type, contact, weight, height, 
           address, gender, date_of_birth, has_ncd, last_donation_date
    FROM donors 
    ORDER BY donor_id DESC
    """
    return execute_query(query, fetch=True)


def get_donor_by_id(donor_id):
    """Get specific donor by ID"""
    query = """
    SELECT donor_id, full_name, blood_type, contact, weight, height, 
           address, gender, date_of_birth, has_ncd, last_donation_date
    FROM donors 
    WHERE donor_id = %s
    """
    return execute_query(query, (donor_id,), fetchone=True)




def update_donor_enhanced(donor_id, full_name, blood_type, contact, weight,
                         height=None, address=None, gender=None, date_of_birth=None, has_ncd=False):
    """Update donor information with enhanced fields"""
    query = """
    UPDATE donors 
    SET full_name = %s, blood_type = %s, contact = %s, weight = %s, 
        height = %s, address = %s, gender = %s, date_of_birth = %s, has_ncd = %s
    WHERE donor_id = %s
    """
    return execute_query(query, (full_name, blood_type, contact, weight, height,
                               address, gender, date_of_birth, has_ncd, donor_id))


# Backward compatibility functions
"""def add_donor(full_name, blood_type, contact, weight):
    Original add donor function for backward compatibility
    query = 
    INSERT INTO donors (full_name, blood_type, contact, weight) 
    VALUES (%s, %s, %s, %s)
    
    return execute_query(query, (full_name, blood_type, contact, weight))"""

def add_donor_enhanced(full_name, blood_type, contact, weight, height, address, gender, date_of_birth, has_ncd):
    """Add new donor with enhanced information - FIXED: removed registration_date"""
    query = "INSERT INTO donors (full_name, blood_type, contact, weight, height, address, gender, date_of_birth, has_ncd) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    return execute_query(query, (full_name, blood_type, contact, weight, height, address, gender, date_of_birth, has_ncd))


def update_donor(donor_id, full_name, blood_type, contact, weight):
    """Original update donor function for backward compatibility"""
    query = """
    UPDATE donors 
    SET full_name = %s, blood_type = %s, contact = %s, weight = %s 
    WHERE donor_id = %s
    """
    return execute_query(query, (full_name, blood_type, contact, weight, donor_id))


def delete_donor(donor_id):
    """Delete donor with transaction handling"""
    conn = get_connection()
    if not conn or not conn.is_connected():
        print("Database connection failed")
        return False

    cursor = None
    try:
        cursor = conn.cursor()

        # Check if donor exists first
        cursor.execute("SELECT donor_id, full_name FROM donors WHERE donor_id=%s", (donor_id,))
        donor = cursor.fetchone()
        if not donor:
            print(f"Donor with ID {donor_id} not found")
            return False

        donor_name = donor[1] if len(donor) > 1 else "Unknown"

        # Start transaction
        conn.start_transaction()

        # Check for foreign key constraints (optional - for debugging)
        cursor.execute("SELECT COUNT(*) FROM donations_history WHERE donor_id=%s", (donor_id,))
        donation_count = cursor.fetchone()[0]
        print(f"Found {donation_count} donation records to delete")

        # Delete from donations_history first (foreign key constraint)
        cursor.execute("DELETE FROM donations_history WHERE donor_id=%s", (donor_id,))
        print(f"Deleted {cursor.rowcount} donation records")

        # Delete donor
        cursor.execute("DELETE FROM donors WHERE donor_id=%s", (donor_id,))
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} donor records")

        if deleted_count == 0:
            conn.rollback()
            print("No donor was deleted, rolling back")
            return False

        conn.commit()
        print(f"Successfully deleted donor {donor_name} (ID: {donor_id})")
        return True

    except Exception as e:
        print(f"Database error in delete_donor: {e}")
        if conn and conn.is_connected():
            conn.rollback()
            print("Transaction rolled back due to error")
        return False
    finally:
        if cursor:
            cursor.close()
        # Do NOT close the connection - it's global
def search_donors(search_term):
    """Search donors by name, blood type, or contact"""
    query = """
    SELECT donor_id, full_name, blood_type, contact, weight, height, 
           address, gender, date_of_birth, has_ncd, last_donation_date
    FROM donors 
    WHERE full_name LIKE %s OR blood_type LIKE %s OR contact LIKE %s
    ORDER BY donor_id DESC
    """
    search_pattern = f"%{search_term}%"
    return execute_query(query, (search_pattern, search_pattern, search_pattern), fetch=True)


# Inventory Functions
def get_inventory():
    """Get all blood inventory"""
    query = "SELECT * FROM inventory ORDER BY blood_type"
    return execute_query(query, fetch=True)


def update_inventory(blood_type, units):
    """Update blood inventory"""
    query = "UPDATE inventory SET units = units + %s WHERE blood_type = %s"
    return execute_query(query, (units, blood_type))


def get_blood_units(blood_type):
    """Get specific blood type units"""
    query = "SELECT units FROM inventory WHERE blood_type = %s"
    result = execute_query(query, (blood_type,), fetchone=True)
    return result['units'] if result else 0


# Donation Functions
def get_donation_history():
    """Get all donation history - FIXED: removed registration_date"""
    query = """
    SELECT d.donor_id, d.full_name, d.blood_type, d.contact, 
           d.last_donation_date, d.weight, d.height, d.gender,
           dh.donation_date, dh.units_collected
    FROM donors d 
    LEFT JOIN donations_history dh ON d.donor_id = dh.donor_id
    WHERE d.last_donation_date IS NOT NULL
    ORDER BY d.last_donation_date DESC
    """
    return execute_query(query, fetch=True)


def get_donor_donation_history(donor_id):
    """Get donation history for a specific donor"""
    query = """
    SELECT donation_date, units_collected
    FROM donations_history
    WHERE donor_id = %s
    ORDER BY donation_date DESC
    """
    return execute_query(query, (donor_id,), fetch=True)


def record_donation(donor_id, donation_date, units=1):
    """Record a new donation with units tracking"""
    try:
        # Start transaction
        conn = get_connection()
        cursor = conn.cursor()
        conn.start_transaction()

        # 1. Update donor's last donation date
        cursor.execute("UPDATE donors SET last_donation_date = %s WHERE donor_id = %s",
                      (donation_date, donor_id))

        # 2. Add to donations_history
        cursor.execute("""
            INSERT INTO donations_history (donor_id, donation_date, units_collected)
            VALUES (%s, %s, %s)
        """, (donor_id, donation_date, units))

        # 3. Get donor's blood type
        cursor.execute("SELECT blood_type FROM donors WHERE donor_id = %s", (donor_id,))
        donor = cursor.fetchone()

        if donor:
            # 4. Add units to inventory
            blood_type = donor[0]
            cursor.execute("UPDATE inventory SET units = units + %s WHERE blood_type = %s",
                          (units, blood_type))

        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error recording donation: {e}")
        if conn and conn.is_connected():
            conn.rollback()
        return False


# Blood Request Functions
def get_blood_requests():
    """Get all blood requests"""
    query = "SELECT * FROM blood_requests ORDER BY request_date DESC"
    return execute_query(query, fetch=True)


def create_blood_request(blood_type, units):
    """Create new blood request"""
    query = """
    INSERT INTO blood_requests (blood_type, units, request_date) 
    VALUES (%s, %s, CURDATE())
    """
    return execute_query(query, (blood_type, units))


def update_request_status(request_id, status):
    """Update blood request status"""
    query = "UPDATE blood_requests SET status = %s WHERE request_id = %s"
    return execute_query(query, (status, request_id))


def fulfill_request(request_id, blood_type, units):
    """Fulfill blood request and update inventory"""
    # Check if enough blood is available
    current_units = get_blood_units(blood_type)
    if current_units >= units:
        # Update inventory
        update_query = "UPDATE inventory SET units = units - %s WHERE blood_type = %s"
        execute_query(update_query, (units, blood_type))

        # Update request status
        update_request_status(request_id, 'Approved')
        return True
    return False


# Dashboard Statistics
def get_dashboard_stats():
    """Get statistics for dashboard"""
    stats = {}

    # Total donors
    query = "SELECT COUNT(*) as total FROM donors"
    result = execute_query(query, fetchone=True)
    stats['total_donors'] = result['total'] if result else 0

    # Total blood units
    query = "SELECT SUM(units) as total FROM inventory"
    result = execute_query(query, fetchone=True)
    stats['total_blood_units'] = result['total'] if result else 0

    # Pending requests
    query = "SELECT COUNT(*) as total FROM blood_requests WHERE status = 'Pending'"
    result = execute_query(query, fetchone=True)
    stats['pending_requests'] = result['total'] if result else 0

    # Today's donations
    query = "SELECT COUNT(*) as total FROM donors WHERE last_donation_date = CURDATE()"
    result = execute_query(query, fetchone=True)
    stats['today_donations'] = result['total'] if result else 0

    # Donors by gender
    query = "SELECT gender, COUNT(*) as count FROM donors GROUP BY gender"
    result = execute_query(query, fetch=True)
    stats['gender_distribution'] = result if result else []

    # Average age of donors
    query = """
    SELECT AVG(YEAR(CURDATE()) - YEAR(date_of_birth)) as avg_age 
    FROM donors 
    WHERE date_of_birth IS NOT NULL
    """
    result = execute_query(query, fetchone=True)
    stats['average_age'] = round(result['avg_age'], 1) if result and result['avg_age'] else 0

    return stats


# ==================== STAFF MANAGEMENT FUNCTIONS ====================
def get_all_staff():
    """Get all staff members"""
    query = "SELECT user_id, username, role FROM users ORDER BY user_id DESC"
    return execute_query(query, fetch=True)


def add_staff_member(username, password, role='staff'):
    """Add new staff member"""
    query = """
    INSERT INTO users (username, password, role) 
    VALUES (%s, %s, %s)
    """
    return execute_query(query, (username, password, role))


def update_staff_member(user_id, username, password, role):
    """Update staff information"""
    try:
        conn = get_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        if password and password.strip():  # If password is provided and not empty
            query = """
            UPDATE users 
            SET username = %s, password = %s, role = %s 
            WHERE user_id = %s
            """
            cursor.execute(query, (username, password, role, user_id))
        else:  # Keep old password
            query = """
            UPDATE users 
            SET username = %s, role = %s 
            WHERE user_id = %s
            """
            cursor.execute(query, (username, role, user_id))

        conn.commit()
        cursor.close()
        return True

    except Exception as e:
        print(f"ERROR in update_staff_member: {e}")
        return False


def delete_staff_member(user_id):
    """Delete staff member"""
    query = "DELETE FROM users WHERE user_id = %s"
    return execute_query(query, (user_id,))


def get_daily_donations_report(date):
    """Get daily donations report data"""
    try:
        # Get all donors who donated on specific date
        query = """
            SELECT d.donor_id, d.full_name, d.blood_type, d.contact, d.weight, d.height,
                   d.gender, d.date_of_birth, d.last_donation_date,
                   dh.units_collected
            FROM donors d 
            JOIN donations_history dh ON d.donor_id = dh.donor_id
            WHERE dh.donation_date = %s
            ORDER BY d.donor_id
        """
        donations = execute_query(query, (date,), fetch=True)

        # Get daily statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_donations,
                COUNT(DISTINCT d.donor_id) as unique_donors,
                SUM(dh.units_collected) as total_units
            FROM donors d 
            JOIN donations_history dh ON d.donor_id = dh.donor_id
            WHERE dh.donation_date = %s
        """
        stats = execute_query(stats_query, (date,), fetchone=True)

        # Get blood type distribution
        blood_dist_query = """
            SELECT 
                d.blood_type,
                COUNT(*) as donation_count,
                SUM(dh.units_collected) as total_units
            FROM donors d 
            JOIN donations_history dh ON d.donor_id = dh.donor_id
            WHERE dh.donation_date = %s
            GROUP BY d.blood_type
            ORDER BY donation_count DESC
        """
        blood_dist = execute_query(blood_dist_query, (date,), fetch=True)

        # Get gender distribution
        gender_dist_query = """
            SELECT 
                d.gender,
                COUNT(*) as donation_count
            FROM donors d 
            JOIN donations_history dh ON d.donor_id = dh.donor_id
            WHERE dh.donation_date = %s
            GROUP BY d.gender
            ORDER BY donation_count DESC
        """
        gender_dist = execute_query(gender_dist_query, (date,), fetch=True)

        return {
            'donations': donations or [],
            'statistics': stats or {},
            'blood_distribution': blood_dist or [],
            'gender_distribution': gender_dist or [],
            'report_date': date
        }

    except Exception as e:
        print(f"Error getting daily report: {e}")
        return None


# Additional utility functions
def get_donor_statistics():
    """Get comprehensive donor statistics"""
    stats = {}

    # Age distribution
    query = """
    SELECT 
        CASE
            WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) < 18 THEN 'Under 18'
            WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) BETWEEN 18 AND 25 THEN '18-25'
            WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) BETWEEN 26 AND 35 THEN '26-35'
            WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) BETWEEN 36 AND 45 THEN '36-45'
            WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) BETWEEN 46 AND 55 THEN '46-55'
            WHEN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) > 55 THEN 'Over 55'
            ELSE 'Unknown'
        END as age_group,
        COUNT(*) as count
    FROM donors
    WHERE date_of_birth IS NOT NULL
    GROUP BY age_group
    ORDER BY FIELD(age_group, 'Under 18', '18-25', '26-35', '36-45', '46-55', 'Over 55', 'Unknown')
    """
    stats['age_distribution'] = execute_query(query, fetch=True)

    # Blood type distribution
    query = "SELECT blood_type, COUNT(*) as count FROM donors GROUP BY blood_type ORDER BY blood_type"
    stats['blood_type_distribution'] = execute_query(query, fetch=True)

    # Donors with NCD
    query = "SELECT COUNT(*) as count FROM donors WHERE has_ncd = TRUE"
    result = execute_query(query, fetchone=True)
    stats['donors_with_ncd'] = result['count'] if result else 0

    # Average weight and height
    query = "SELECT AVG(weight) as avg_weight, AVG(height) as avg_height FROM donors WHERE weight > 0"
    result = execute_query(query, fetchone=True)
    stats['avg_weight'] = round(result['avg_weight'], 1) if result and result['avg_weight'] else 0
    stats['avg_height'] = round(result['avg_height'], 1) if result and result['avg_height'] else 0

    return stats


def update_existing_donors():
    """Update existing donors table to add new columns if they don't exist"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check and add missing columns
        columns_to_add = [
            ("height", "DECIMAL(5,2)"),
            ("address", "TEXT"),
            ("gender", "VARCHAR(10)"),
            ("date_of_birth", "DATE"),
            ("has_ncd", "BOOLEAN DEFAULT FALSE"),
            ("registration_date", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")  # ADDED THIS LINE
        ]

        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE donors ADD COLUMN {column_name} {column_type}")
                print(f"Added column {column_name} to donors table")
            except Error as e:
                # Column might already exist
                if "Duplicate column name" not in str(e):
                    print(f"Error adding column {column_name}: {e}")

        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error updating donors table: {e}")
        return False


# Initialize database with enhanced structure
if __name__ == "__main__":
    connect_db()
    update_existing_donors()
    print("Database setup complete with enhanced donor fields")