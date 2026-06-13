import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import database

global message

def create_donors_window(root, user, go_back):
    """Create donors management window"""
    clear_window(root)

    root.title("Blood Donation System - Manage Donors")
    root.geometry("1300x700")  # Increased size for more fields

    # Title
    tk.Label(root, text="Manage Donors", font=("Arial", 20, "bold"),
             bg="#f0f0f0").pack(pady=10)

    # Search frame
    search_frame = tk.Frame(root, bg="#f0f0f0")
    search_frame.pack(fill=tk.X, padx=20, pady=10)

    tk.Label(search_frame, text="Search:", font=("Arial", 12),
             bg="#f0f0f0").pack(side=tk.LEFT)

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var,
                            font=("Arial", 12), width=30)
    search_entry.pack(side=tk.LEFT, padx=10)

    def search_donors_func():
        """Search donors"""
        search_term = search_var.get().strip()
        load_donors(search_term)

    tk.Button(search_frame, text="Search", font=("Arial", 10),
              bg="#4CAF50", fg="white", command=search_donors_func
              ).pack(side=tk.LEFT, padx=5)

    tk.Button(search_frame, text="Refresh", font=("Arial", 10),
              bg="#2196F3", fg="white", command=lambda: load_donors()
              ).pack(side=tk.LEFT)

    # Table frame with scrollbars
    table_frame = tk.Frame(root)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Create treeview with additional columns
    columns = ("ID", "Name", "Blood Type", "Gender", "Contact", "Age",
               "Last Donation", "Weight", "Height", "NCD", "Address")

    donor_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

    # Configure columns with widths
    col_widths = [60, 150, 80, 60, 100, 50, 100, 60, 60, 50, 150]
    for col, width in zip(columns, col_widths):
        donor_tree.heading(col, text=col)
        donor_tree.column(col, width=width, minwidth=50)

    # Scrollbars
    y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=donor_tree.yview)
    x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=donor_tree.xview)
    donor_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

    y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    donor_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def load_donors(search_term=""):
        """Load donors into treeview"""
        # Clear existing items
        for item in donor_tree.get_children():
            donor_tree.delete(item)

        if search_term:
            donors = database.search_donors(search_term)
        else:
            donors = database.get_all_donors()

        if donors:
            for donor in donors:
                # Calculate age from date of birth if available
                age = "N/A"
                if donor.get('date_of_birth'):
                    from datetime import datetime
                    try:
                        birth_date = datetime.strptime(str(donor['date_of_birth']), '%Y-%m-%d')
                        today = datetime.now()
                        age = today.year - birth_date.year - (
                                    (today.month, today.day) < (birth_date.month, birth_date.day))
                        age = str(age)
                    except:
                        age = "N/A"

                donor_tree.insert("", tk.END, values=(
                    donor['donor_id'],
                    donor['full_name'],
                    donor['blood_type'],
                    donor.get('gender', 'N/A'),
                    donor['contact'] or "N/A",
                    age,
                    donor['last_donation_date'] or "Never",
                    donor['weight'] or "N/A",
                    donor.get('height', 'N/A'),
                    "Yes" if donor.get('has_ncd') else "No",
                    donor.get('address', 'N/A')[:20] + "..." if donor.get('address') and len(
                        donor['address']) > 20 else donor.get('address', 'N/A')
                ))
        else:
            # Show empty message
            donor_tree.insert("", tk.END, values=("No donors found", "", "", "", "", "", "", "", "", "", ""))

    # Load initial data
    load_donors()

    def add_donor_func():
        """Open add donor form"""
        show_donor_form()

    def edit_donor_func():
        """Edit selected donor"""
        selection = donor_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a donor to edit")
            return

        donor_id = donor_tree.item(selection[0])['values'][0]
        show_donor_form(donor_id)

    def delete_donor_func():
        """Delete selected donor"""
        selection = donor_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a donor to delete")
            return

        # Debug: Print selection details
        print(f"Selected items: {selection}")

        donor_id = donor_tree.item(selection[0])['values'][0]
        donor_name = donor_tree.item(selection[0])['values'][1]

        print(f"Attempting to delete donor: ID={donor_id}, Name={donor_name}")

        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Are you sure you want to delete {donor_name}?\n\nID: {donor_id}")

        if confirm:
            print(f"Calling database.delete_donor({donor_id})")
            try:
                result = database.delete_donor(donor_id)
                print(f"Delete result: {result}")

                if result:
                    messagebox.showinfo("Success", "Donor deleted successfully")
                    load_donors()  # Refresh the treeview
                else:
                    messagebox.showerror("Error",
                                         f"Failed to delete {donor_name}.\n\nPossible reasons:\n"
                                         f"1. Donor doesn't exist in database\n"
                                         f"2. Database connection issue\n"
                                         f"3. Foreign key constraint violation")
            except Exception as e:
                print(f"Exception during delete: {e}")
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def record_donation_func():
        """Record donation for selected donor"""
        selection = donor_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a donor")
            return

        donor_id = donor_tree.item(selection[0])['values'][0]
        donor_name = donor_tree.item(selection[0])['values'][1]

        # Check if donor has NCD
        donor_info = donor_tree.item(selection[0])['values']
        has_ncd = donor_info[9] if len(donor_info) > 9 else "No"

        if has_ncd == "Yes":
            response = messagebox.askyesno("Medical Warning",
                                           f"Donor {donor_name} has non-communicable diseases.\n"
                                           f"Are you sure you want to proceed with donation?")
            if not response:
                return

        # Create donation window
        donation_window = tk.Toplevel(root)
        donation_window.title(f"Record Donation for {donor_name}")
        donation_window.geometry("400x300")

        tk.Label(donation_window, text=f"Record donation for:",
                 font=("Arial", 12)).pack(pady=10)
        tk.Label(donation_window, text=donor_name,
                 font=("Arial", 14, "bold")).pack(pady=5)

        # Donation date
        tk.Label(donation_window, text="Donation Date:",
                 font=("Arial", 11)).pack(pady=10)

        date_entry = DateEntry(donation_window, width=12,
                               date_pattern='yyyy-mm-dd')
        date_entry.pack(pady=5)

        # Blood units collected
        tk.Label(donation_window, text="Units Collected:",
                 font=("Arial", 11)).pack(pady=10)

        units_var = tk.StringVar(value="1")
        units_spinbox = tk.Spinbox(donation_window, from_=1, to=4, textvariable=units_var,
                                   font=("Arial", 11), width=5)
        units_spinbox.pack(pady=5)

        def save_donation():
            """Save donation record"""
            donation_date = date_entry.get()
            units = int(units_var.get())

            result = database.record_donation(donor_id, donation_date, units)
            if result:
                messagebox.showinfo("Success", f"{units} unit(s) donation recorded successfully")
                donation_window.destroy()
                load_donors()
            else:
                messagebox.showerror("Error", "Failed to record donation")

        # Buttons
        button_frame = tk.Frame(donation_window)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Record Donation",
                  font=("Arial", 11, "bold"),
                  bg="#4CAF50", fg="white", command=save_donation
                  ).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="Cancel", font=("Arial", 11),
                  bg="#757575", fg="white", command=donation_window.destroy
                  ).pack(side=tk.LEFT, padx=10)

    def show_donor_form(donor_id=None):
        """Show donor form for add/edit"""
        form_window = tk.Toplevel(root)
        form_window.title("Add Donor" if not donor_id else "Edit Donor")
        form_window.geometry("600x700")  # Larger window for more fields

        # Create scrollable frame
        main_frame = tk.Frame(form_window)
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Form title
        title_text = "Add New Donor" if not donor_id else "Edit Donor"
        tk.Label(scrollable_frame, text=title_text,
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=20, padx=20)

        # Form fields
        row = 1

        # Full Name
        tk.Label(scrollable_frame, text="Full Name:*", font=("Arial", 11)
                 ).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        name_var = tk.StringVar()
        name_entry = tk.Entry(scrollable_frame, textvariable=name_var, font=("Arial", 11), width=30)
        name_entry.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        row += 1

        # Date of Birth
        tk.Label(scrollable_frame, text="Date of Birth:*", font=("Arial", 11)
                 ).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)

        # Create a frame for date entry
        dob_frame = tk.Frame(scrollable_frame)
        dob_frame.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)

        # Use a simpler date entry (3 separate fields for day, month, year)
        tk.Label(dob_frame, text="Year:").pack(side=tk.LEFT)
        year_var = tk.StringVar(value="1990")
        year_spin = tk.Spinbox(dob_frame, from_=1900, to=2024, textvariable=year_var,
                               width=5, font=("Arial", 11))
        year_spin.pack(side=tk.LEFT, padx=5)

        tk.Label(dob_frame, text="Month:").pack(side=tk.LEFT)
        month_var = tk.StringVar(value="1")
        month_spin = tk.Spinbox(dob_frame, from_=1, to=12, textvariable=month_var,
                                width=3, font=("Arial", 11))
        month_spin.pack(side=tk.LEFT, padx=5)

        tk.Label(dob_frame, text="Day:").pack(side=tk.LEFT)
        day_var = tk.StringVar(value="1")
        day_spin = tk.Spinbox(dob_frame, from_=1, to=31, textvariable=day_var,
                              width=3, font=("Arial", 11))
        day_spin.pack(side=tk.LEFT, padx=5)
        row += 1

        # Gender
        tk.Label(scrollable_frame, text="Gender:*", font=("Arial", 11)
                 ).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        gender_var = tk.StringVar(value="Male")
        gender_frame = tk.Frame(scrollable_frame)
        gender_frame.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)

        tk.Radiobutton(gender_frame, text="Male", variable=gender_var,
                       value="Male").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(gender_frame, text="Female", variable=gender_var,
                       value="Female").pack(side=tk.LEFT, padx=10)
        row += 1

        # Blood Type
        tk.Label(scrollable_frame, text="Blood Type:*", font=("Arial", 11)
                 ).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        blood_type_var = tk.StringVar()
        blood_type_combo = ttk.Combobox(
            scrollable_frame,
            textvariable=blood_type_var,
            values=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            state="readonly",
            width=28,
            font=("Arial", 11)
        )
        blood_type_combo.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        blood_type_combo.current(0)
        row += 1

        # Contact
        tk.Label(scrollable_frame, text="Contact:*", font=("Arial", 11)
                 ).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        contact_var = tk.StringVar()
        contact_entry = tk.Entry(scrollable_frame, textvariable=contact_var,
                                 font=("Arial", 11), width=30)
        contact_entry.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        row += 1

        # Address
        tk.Label(scrollable_frame, text="Address:", font=("Arial", 11)
                 ).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        address_var = tk.StringVar()
        address_text = tk.Text(scrollable_frame, height=3, width=30, font=("Arial", 11))
        address_text.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        row += 1

        # Weight
        tk.Label(scrollable_frame, text="Weight (kg):*", font=("Arial", 11)
                 ).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        weight_var = tk.StringVar()
        weight_entry = tk.Entry(scrollable_frame, textvariable=weight_var,
                                font=("Arial", 11), width=30)
        weight_entry.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        row += 1

        # Height
        tk.Label(scrollable_frame, text="Height (cm):", font=("Arial", 11)
                 ).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        height_var = tk.StringVar()
        height_entry = tk.Entry(scrollable_frame, textvariable=height_var,
                                font=("Arial", 11), width=30)
        height_entry.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        row += 1

        # Non-communicable Diseases
        tk.Label(scrollable_frame, text="Non-communicable Diseases:",
                 font=("Arial", 11)).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        ncd_var = tk.BooleanVar()
        ncd_check = tk.Checkbutton(scrollable_frame, text="Has NCD",
                                   variable=ncd_var, font=("Arial", 11))
        ncd_check.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        row += 1

        # Previous Donation History
        """"tk.Label(scrollable_frame, text="Previous Donation:",
                 font=("Arial", 11)).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        prev_donation_var = tk.BooleanVar(value=False)
        prev_donation_check = tk.Checkbutton(scrollable_frame, text="Previously donated",
                                             variable=prev_donation_var, font=("Arial", 11))
        prev_donation_check.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        row += 1"""

        # Last Donation Date (if previously donated)
        tk.Label(scrollable_frame, text="Last Donation Date:",
                 font=("Arial", 11)).grid(row=row, column=0, padx=20, pady=10, sticky=tk.E)
        last_donation_var = tk.StringVar()
        last_donation_entry = DateEntry(scrollable_frame, textvariable=last_donation_var,
                                        width=12, date_pattern='yyyy-mm-dd',
                                        font=("Arial", 11))
        last_donation_entry.grid(row=row, column=1, padx=10, pady=10, sticky=tk.W)
        row += 1

        # Load donor data if editing
        if donor_id:
            # Find donor in treeview
            for item in donor_tree.get_children():
                if donor_tree.item(item)['values'][0] == donor_id:
                    donor = donor_tree.item(item)['values']
                    break

            if donor:
                name_var.set(donor[1])
                blood_type_var.set(donor[2])
                contact_var.set(donor[4])
                weight_var.set(donor[7])

                # Set other fields if available
                if len(donor) > 8:
                    # Height
                    if donor[8] and donor[8] != "N/A":
                        height_var.set(donor[8])
                    # NCD
                    ncd_var.set(donor[9] == "Yes")
                    # Address
                    if len(donor) > 10 and donor[10] and donor[10] != "N/A":
                        address_text.delete("1.0", tk.END)
                        address_text.insert("1.0", donor[10])

        def save_donor():
            """Save donor data"""

            name = name_var.get().strip()
            blood_type = blood_type_var.get()
            contact = contact_var.get().strip()
            weight = weight_var.get().strip()
            height = height_var.get().strip()
            address = address_text.get("1.0", tk.END).strip()
            has_ncd = ncd_var.get()
            gender = gender_var.get()

            # Create date of birth string
            try:
                dob = f"{year_var.get()}-{month_var.get().zfill(2)}-{day_var.get().zfill(2)}"
            except:
                dob = ""

            if not name:
                messagebox.showwarning("Validation Error", "Please enter donor name")
                return

            if not contact:
                messagebox.showwarning("Validation Error", "Please enter contact information")
                return

            try:
                weight_float = float(weight) if weight else 0
                height_float = float(height) if height else 0
            except ValueError:
                messagebox.showerror("Input Error", "Please enter valid numbers for weight and height")
                return

            # Use the enhanced database function if available, otherwise use basic one
            try:
                if donor_id:
                    # Try to update with enhanced function
                    result = database.update_donor_enhanced(
                        donor_id, name, blood_type, contact, weight_float,
                        height_float, address, gender, dob, has_ncd
                    )
                    message = "Donor updated successfully!"
                else:
                    # Try to add with enhanced function
                    result = database.add_donor_enhanced(
                        name, blood_type, contact, weight_float,
                        height_float, address, gender, dob, has_ncd
                    )
                    message = "Donor added successfully!"
            except:
                # Fallback to basic function if enhanced not available
                if donor_id:
                    result = database.update_donor(donor_id, name, blood_type, contact, weight_float)
                else:
                    result = database.add_donor(name, blood_type, contact, weight_float)

            if result:
                messagebox.showinfo("Success", message)
                form_window.destroy()
                load_donors()
            else:
                messagebox.showerror("Error", "Failed to save donor")

        # Buttons
        button_frame = tk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Save",
                  font=("Arial", 11, "bold"),
                  bg="#4CAF50", fg="white", width=15,
                  command=save_donor).pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="Cancel", font=("Arial", 11),
                  bg="#757575", fg="white", width=15,
                  command=form_window.destroy).pack(side=tk.LEFT, padx=10)

        # Configure grid weights
        scrollable_frame.columnconfigure(1, weight=1)

    # Action buttons
    action_frame = tk.Frame(root, bg="#f0f0f0")
    action_frame.pack(pady=10)

    buttons = [
        ("Add New Donor", add_donor_func, "#388E3C"),
        ("Edit Donor", edit_donor_func, "#FF9800"),
        ("Delete Donor", delete_donor_func, "#f44336"),
        ("Record Donation", record_donation_func, "#2196F3"),
        ("Export to CSV", lambda: export_to_csv(donor_tree), "#9C27B0"),
        ("Back to Dashboard", go_back, "#757575")
    ]

    for text, command, color in buttons:
        tk.Button(action_frame, text=text, font=("Arial", 10),
                  bg=color, fg="white", command=command
                  ).pack(side=tk.LEFT, padx=5)


def export_to_csv(tree):
    """Export donor data to CSV"""
    import csv
    from tkinter import filedialog

    filename = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title="Save donor data as CSV"
    )

    if filename:
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write headers
                headers = [tree.heading(col)['text'] for col in tree['columns']]
                writer.writerow(headers)

                # Write data
                for item in tree.get_children():
                    writer.writerow(tree.item(item)['values'])

            messagebox.showinfo("Success", f"Donor data exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")


def clear_window(root):
    """Clear all widgets from window"""
    for widget in root.winfo_children():
        widget.destroy()