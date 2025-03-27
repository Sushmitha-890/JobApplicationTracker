import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import hashlib
import os
import base64
from datetime import datetime

# CSV Files for Data and Credentials
csv_file = "job_applications.csv"
credentials_file = "credentials.csv"

# Global variables
current_window = None
history_table = None
username = None
root = None

# Improved Password Hashing Function
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).digest()
    return salt, hashed_password

# Verify Password Function
def verify_password(stored_salt, stored_hash, provided_password):
    _, new_hash = hash_password(provided_password, stored_salt)
    return new_hash == stored_hash

# Open Visualization Window
def open_visualizations(username):
    viz_window = ttk.Toplevel(root)
    viz_window.title(f"📊 Job Application Statistics - {username}")
    viz_window.geometry("1000x600")

    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Filter data for the current user
    user_data = df[df["User Name"] == username]
    
    # Create a matplotlib figure with two sophisticated subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(f'Job Application Insights for {username}', fontsize=16)
    
    # Left Plot: Comprehensive Status Breakdown with Trend
    # Prepare data for status progression
    user_data['Date Applied'] = pd.to_datetime(user_data['Date Applied'])
    user_data_sorted = user_data.sort_values('Date Applied')
    
    # Status color mapping
    status_colors = {
        'Applied': '#2196F3',      # Blue
        'Interview': '#4CAF50',    # Green
        'Rejected': '#F44336',     # Red
        'Hired': '#9C27B0'         # Purple
    }
    
    # Cumulative status count over time
    status_progression = user_data_sorted.groupby([
        pd.Grouper(key='Date Applied', freq='W'), 'Status'
    ]).size().unstack(fill_value=0).cumsum()
    
    # Plot stacked area chart
    status_progression.plot(kind='area', stacked=True, ax=ax1, 
                             color=[status_colors.get(col, '#607D8B') for col in status_progression.columns])
    ax1.set_title('Job Application Status Progression')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Cumulative Applications')
    ax1.legend(title='Status', loc='upper left')
    
    # Right Plot: Pie Chart with Advanced Styling
    # Calculate status percentages
    status_counts = user_data['Status'].value_counts()
    
    # Create a more sophisticated pie chart
    wedges, texts, autotexts = ax2.pie(
        status_counts, 
        labels=status_counts.index, 
        autopct='%1.1f%%',
        colors=[status_colors.get(status, '#607D8B') for status in status_counts.index],
        wedgeprops=dict(width=0.6, edgecolor='white'),
        pctdistance=0.85
    )
    
    # Style the percentage text
    plt.setp(autotexts, size=9, weight="bold", color="white")
    
    ax2.set_title('Application Status Distribution')
    
    # Add a legend with total counts
    legend_labels = [f'{status} ({count})' for status, count in status_counts.items()]
    ax2.legend(wedges, legend_labels, title="Status Breakdown", 
               loc="center left", bbox_to_anchor=(1, 0.5))
    
    # Adjust layout
    plt.tight_layout()
    
    # Embed matplotlib figure in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=viz_window)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill='both', expand=True)

# Export Applications Function
def export_applications(username):
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Filter data for the current user
    user_data = df[df["User Name"] == username]
    
    # Ask user for export location
    export_filename = simpledialog.askstring("Export", "Enter export filename (without extension):", 
                                             initialvalue=f"{username}_job_applications")
    
    if export_filename:
        try:
            # Export to different formats
            export_formats = [
                ('Excel', 'xlsx'),
                ('CSV', 'csv'),
                ('PDF', 'pdf')
            ]
            
            for format_name, extension in export_formats:
                full_filename = f"{export_filename}.{extension}"
                
                if extension == 'xlsx':
                    user_data.to_excel(full_filename, index=False)
                elif extension == 'csv':
                    user_data.to_csv(full_filename, index=False)
                elif extension == 'pdf':
                    from reportlab.lib.pagesizes import letter
                    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
                    from reportlab.lib import colors
                    
                    doc = SimpleDocTemplate(full_filename, pagesize=letter)
                    data = [user_data.columns.tolist()] + user_data.values.tolist()
                    table = Table(data)
                    
                    # Add style
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.grey),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,0), 12),
                        ('BOTTOMPADDING', (0,0), (-1,0), 12),
                        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                        ('GRID', (0,0), (-1,-1), 1, colors.black)
                    ]))
                    
                    doc.build([table])
            
            messagebox.showinfo("Export Successful", 
                                f"Applications exported in XLSX, CSV, and PDF formats!")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred: {str(e)}")

# Delete Application Function
def delete_application(history_table, username):
    # Get selected item
    try:
        selected_item = history_table.selection()
        
        if not selected_item:
            messagebox.showwarning("Delete Error", "Please select an application to delete.")
            return
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this application?"):
            # Get the values of the selected row
            selected_values = history_table.item(selected_item[0])['values']
            
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Filter out the row to delete
            df = df[~((df["User Name"] == username) & 
                      (df["Company"] == selected_values[0]) & 
                      (df["Position"] == selected_values[1]) & 
                      (df["Date Applied"] == selected_values[2]))]
            
            # Save the updated DataFrame
            df.to_csv(csv_file, index=False)
            
            # Update the history table
            update_history_table(history_table, username)
            
            messagebox.showinfo("Success", "Application deleted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while deleting: {str(e)}")

# Update History Table
def update_history_table(history_table, current_username):
    # Clear existing items
    for row in history_table.get_children():
        history_table.delete(row)

    # Read CSV and filter for current user
    df = pd.read_csv(csv_file)
    user_data = df[df["User Name"] == current_username]

    # Insert user's applications
    for index, row in user_data.iterrows():
        history_table.insert("", "end", values=(
            row["Company"], 
            row["Position"], 
            row["Date Applied"], 
            row["Status"]
        ))

# Login/Register Window Function
def show_login_register_window(is_register=False):
    global current_window, root

    # Close any existing login/register window
    if current_window:
        try:
            current_window.destroy()
        except:
            pass

    # Create new login/register window
    current_window = ttk.Toplevel(root)
    current_window.title("Job Tracker - Career Management")
    current_window.geometry("500x600")  # Increased height and width
    current_window.protocol("WM_DELETE_WINDOW", root.quit)

    # Background and Style
    style = ttk.Style()
    style.configure('TFrame', background='#f0f0f0')

    # Main Container
    main_container = ttk.Frame(current_window)
    main_container.pack(fill='both', expand=True, padx=20, pady=20)

    # Logo Section
    logo_frame = ttk.Frame(main_container)
    logo_frame.pack(pady=(0, 20))

    # Job Tracking Icons
    def create_icon_label(parent, text, emoji):
        label = ttk.Label(parent, text=f"{emoji} {text}", 
                          font=("Arial", 10), 
                          bootstyle=INFO)
        return label

    icon_container = ttk.Frame(logo_frame)
    icon_container.pack(fill='x', expand=True)

    # Create and place job tracking icons
    create_icon_label(icon_container, "Track Jobs", "🔍").pack(side='left', padx=10)
    create_icon_label(icon_container, "Manage Applications", "💼").pack(side='left', padx=10)
    create_icon_label(icon_container, "Visualize Progress", "📊").pack(side='left', padx=10)

    # Main Title
    ttk.Label(main_container, text="🚀 Job Application Tracker", 
              font=("Arial", 20, "bold"), 
              bootstyle=PRIMARY).pack(pady=(0, 20))

    # Username
    ttk.Label(main_container, text="Username:").pack(pady=5)
    username_entry = ttk.Entry(main_container, width=40)
    username_entry.pack(pady=5)

    # Password
    ttk.Label(main_container, text="Password:").pack(pady=5)
    password_entry = ttk.Entry(main_container, show="*", width=40)
    password_entry.pack(pady=5)

    # Login Function
    def login():
        username = username_entry.get().strip()
        password = password_entry.get()

        # Validate input
        if not username or not password:
            messagebox.showwarning("Input Error", "Both username and password are required!")
            return

        try:
            # Load credentials
            credentials_df = pd.read_csv(credentials_file)
            
            # Find user
            user = credentials_df[credentials_df['Username'] == username]
            
            if user.empty:
                messagebox.showwarning("Login Failed", "User not found.")
                return

            # Decode salt and password hash
            stored_salt = base64.b64decode(user['Salt'].values[0])
            stored_hash = base64.b64decode(user['PasswordHash'].values[0])

            # Verify password
            if verify_password(stored_salt, stored_hash, password):
                current_window.destroy()  # Close login window
                show_main_window(username)
            else:
                messagebox.showwarning("Login Failed", "Invalid username or password.")

        except FileNotFoundError:
            messagebox.showerror("Error", "Credentials file not found. Please register first.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    # Register Function
    def register():
        username = username_entry.get().strip()
        password = password_entry.get()

        # Validate input
        if not username or not password:
            messagebox.showwarning("Input Error", "Both username and password are required!")
            return

        # Load existing credentials
        try:
            credentials_df = pd.read_csv(credentials_file)
        except FileNotFoundError:
            credentials_df = pd.DataFrame(columns=["Username", "Salt", "PasswordHash"])

        # Check if user already exists
        if not credentials_df[credentials_df['Username'] == username].empty:
            messagebox.showwarning("Registration Failed", "Username already exists. Please choose another.")
            return

        # Password complexity checks
        if len(password) < 8:
            messagebox.showwarning("Weak Password", "Password must be at least 8 characters long.")
            return

        # Hash the password
        salt, password_hash = hash_password(password)

        # Prepare new user data
        new_user = pd.DataFrame({
            'Username': [username],
            'Salt': [base64.b64encode(salt).decode('utf-8')],
            'PasswordHash': [base64.b64encode(password_hash).decode('utf-8')]
        })

        # Append new user and save
        credentials_df = pd.concat([credentials_df, new_user], ignore_index=True)
        credentials_df.to_csv(credentials_file, index=False)

        messagebox.showinfo("Success", "User registered successfully!")
        
        # Switch to login view after successful registration
        switch_to_login()

    # Switch between Login and Register views
    def switch_to_login():
        # Clear entries
        username_entry.delete(0, 'end')
        password_entry.delete(0, 'end')
        
        # Remove existing buttons
        for widget in button_frame.winfo_children():
            widget.destroy()
        
        # Login buttons
        login_btn = ttk.Button(button_frame, text="Login", command=login, bootstyle=PRIMARY)
        login_btn.pack(side='left', padx=5, expand=True)
        
        register_view_btn = ttk.Button(button_frame, text="Register New Account", 
                   command=switch_to_register, 
                   bootstyle=SUCCESS)
        register_view_btn.pack(side='left', padx=5, expand=True)

    def switch_to_register():
        # Clear entries
        username_entry.delete(0, 'end')
        password_entry.delete(0, 'end')
        
        # Remove existing buttons
        for widget in button_frame.winfo_children():
            widget.destroy()
        
        # Register buttons
        register_btn = ttk.Button(button_frame, text="Register", command=register, bootstyle=SUCCESS)
        register_btn.pack(side='left', padx=5, expand=True)
        
        login_view_btn = ttk.Button(button_frame, text="Back to Login", 
                   command=switch_to_login, 
                   bootstyle=PRIMARY)
        login_view_btn.pack(side='left', padx=5, expand=True)

    # Button Frame
    button_frame = ttk.Frame(main_container)
    button_frame.pack(pady=10)

    # Additional motivational text
    motivation_text = ttk.Label(main_container, 
                                text="Your Career Journey Starts Here!", 
                                font=("Arial", 12, "italic"),
                                bootstyle=SECONDARY)
    motivation_text.pack(pady=(20, 10))

    # Determine initial view based on is_register parameter
    if is_register:
        switch_to_register()
    else:
        switch_to_login()

# Show Main Window Function (With Search Functionality)
def show_main_window(current_username):
    global current_window, history_table, username
    username = current_username
    
    if current_window:
        current_window.destroy()  # Close the previous window if open

    # Load or Create Data
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["User Name", "Company", "Position", "Date Applied", "Status"])
        df.to_csv(csv_file, index=False)

    # Main Application Window
    current_window = ttk.Toplevel(root)
    current_window.title("🚀 Job Application Tracker")
    current_window.geometry("1200x900")

    # Style and Background
    style = ttk.Style()
    style.configure('Custom.TFrame', background='#f0f0f0')

    # Main Container
    main_container = ttk.Frame(current_window, style='Custom.TFrame')
    main_container.pack(fill='both', expand=True, padx=20, pady=20)

    # Title
    title_label = ttk.Label(main_container, text="🚀 Job Application Tracker", 
                             font=("Arial", 20, "bold"), 
                             bootstyle=PRIMARY)
    title_label.pack(pady=(0, 20))

    # Form Frame
    form_frame = ttk.LabelFrame(main_container, text="Add New Application", bootstyle=SUCCESS)
    form_frame.pack(fill='x', pady=10)

    # Input Fields
    inputs_container = ttk.Frame(form_frame)
    inputs_container.pack(padx=10, pady=10, fill='x')

    # Company Name
    ttk.Label(inputs_container, text="Company Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
    company_entry = ttk.Entry(inputs_container, width=40)
    company_entry.grid(row=0, column=1, padx=5, pady=5)

    # Position
    ttk.Label(inputs_container, text="Position:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
    job_roles = ["Software Engineer", "Data Analyst", "Web Developer", "Machine Learning Engineer", 
                 "Cybersecurity Analyst", "Project Manager", "DevOps Engineer", "Other"]
    position_var = ttk.StringVar(value=job_roles[0])
    position_dropdown = ttk.Combobox(inputs_container, textvariable=position_var, 
                                     values=job_roles, width=37)
    position_dropdown.grid(row=1, column=1, padx=5, pady=5)

    # Date Applied
    ttk.Label(inputs_container, text="Date Applied:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
    date_entry = ttk.Entry(inputs_container, width=40)
    date_entry.grid(row=2, column=1, padx=5, pady=5)
    date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

    # Status
    ttk.Label(inputs_container, text="Status:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
    status_var = ttk.StringVar(value="Applied")
    status_dropdown = ttk.Combobox(inputs_container, textvariable=status_var, 
                                   values=["Applied", "Interview", "Rejected", "Hired"], width=37)
    status_dropdown.grid(row=3, column=1, padx=5, pady=5)

    # Add Button
    def add_application():
        company = company_entry.get().strip()
        position = position_dropdown.get()
        date_applied = date_entry.get().strip()
        status = status_var.get()

        if not all([company, position, date_applied, status]):
            messagebox.showwarning("Input Error", "All fields must be filled!")
            return

        # Read current dataframe
        df = pd.read_csv(csv_file)

        # Create new row
        new_row = pd.DataFrame({
            "User Name": [username],
            "Company": [company],
            "Position": [position],
            "Date Applied": [date_applied],
            "Status": [status]
        })

        # Concatenate new row
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save to CSV
        df.to_csv(csv_file, index=False)

        # Update history table
        update_history_table(history_table, username)

        # Clear input fields
        company_entry.delete(0, 'end')
        position_dropdown.set(job_roles[0])
        date_entry.delete(0, 'end')
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        status_var.set("Applied")

        messagebox.showinfo("Success", "Application Added Successfully!")

    add_btn = ttk.Button(inputs_container, text="➕ Add Application", 
                         command=add_application, bootstyle=SUCCESS)
    add_btn.grid(row=4, column=0, columnspan=2, pady=10)

    # Search Frame
    search_frame = ttk.LabelFrame(main_container, text="Search Applications", bootstyle=INFO)
    search_frame.pack(fill='x', pady=10)

    # Search Inputs Container
    search_container = ttk.Frame(search_frame)
    search_container.pack(padx=10, pady=10, fill='x')

    # Company Search
    ttk.Label(search_container, text="Company:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
    company_search_entry = ttk.Entry(search_container, width=30)
    company_search_entry.grid(row=0, column=1, padx=5, pady=5)

    # Date Search
    ttk.Label(search_container, text="Date From:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
    date_from_entry = ttk.Entry(search_container, width=20)
    date_from_entry.grid(row=0, column=3, padx=5, pady=5)
    date_from_entry.insert(0, "YYYY-MM-DD")

    ttk.Label(search_container, text="Date To:").grid(row=0, column=4, sticky='w', padx=5, pady=5)
    date_to_entry = ttk.Entry(search_container, width=20)
    date_to_entry.grid(row=0, column=5, padx=5, pady=5)
    date_to_entry.insert(0, "YYYY-MM-DD")

    # Search Function
    def perform_search():
        # Read CSV
        df = pd.read_csv(csv_file)
        
        # Filter for current user
        user_data = df[df["User Name"] == username]
        
        # Get search parameters
        company_search = company_search_entry.get().strip().lower()
        date_from = date_from_entry.get().strip()
        date_to = date_to_entry.get().strip()
        
        # Apply filters
        if company_search:
            user_data = user_data[user_data['Company'].str.lower().str.contains(company_search, case=False, na=False)]
        
        if date_from != "YYYY-MM-DD" and date_from:
            user_data = user_data[pd.to_datetime(user_data['Date Applied']) >= pd.to_datetime(date_from)]
        
        if date_to != "YYYY-MM-DD" and date_to:
            user_data = user_data[pd.to_datetime(user_data['Date Applied']) <= pd.to_datetime(date_to)]
        
        # Clear existing table
        for row in history_table.get_children():
            history_table.delete(row)
        
        # Insert filtered results
        for index, row in user_data.iterrows():
            history_table.insert("", "end", values=(
                row["Company"], 
                row["Position"], 
                row["Date Applied"], 
                row["Status"]
            ))
        
        # Show results count
        result_count = len(user_data)
        messagebox.showinfo("Search Results", f"Found {result_count} matching applications.")

    # Reset Search Function
    def reset_search():
        # Clear search entries
        company_search_entry.delete(0, 'end')
        date_from_entry.delete(0, 'end')
        date_from_entry.insert(0, "YYYY-MM-DD")
        date_to_entry.delete(0, 'end')
        date_to_entry.insert(0, "YYYY-MM-DD")
        
        # Reload full table for current user
        update_history_table(history_table, username)

    # Search Buttons
    search_btn = ttk.Button(search_container, text="🔍 Search", 
                             command=perform_search, bootstyle=INFO)
    search_btn.grid(row=0, column=6, padx=5, pady=5)

    reset_btn = ttk.Button(search_container, text="↩️ Reset", 
                           command=reset_search, bootstyle=SECONDARY)
    reset_btn.grid(row=0, column=7, padx=5, pady=5)

    # History Table Frame
    table_frame = ttk.LabelFrame(main_container, text="Application History", bootstyle=PRIMARY)
    table_frame.pack(fill='both', expand=True, pady=10)

    # Columns
    columns = ["Company", "Position", "Date Applied", "Status"]
    history_table = ttk.Treeview(table_frame, columns=columns, show="headings")

    # Configure columns
    for col in columns:
        history_table.heading(col, text=col)
        history_table.column(col, anchor="center", width=150)

    history_table.pack(fill='both', expand=True, padx=10, pady=10)

    # Button Frame
    button_frame = ttk.Frame(table_frame)
    button_frame.pack(pady=10)

    # Delete Button
    delete_btn = ttk.Button(button_frame, text="🗑️ Delete Application", 
                            command=lambda: delete_application(history_table, username), 
                            bootstyle=DANGER)
    delete_btn.pack(side='left', padx=5)

    # Visualization Button
    viz_btn = ttk.Button(button_frame, text="📊 View Statistics", 
                         command=lambda current_user=current_username: open_visualizations(current_user), 
                         bootstyle=INFO)
    viz_btn.pack(side='left', padx=5)

    # Export Button
    export_btn = ttk.Button(button_frame, text="📥 Export Applications", 
                            command=lambda current_user=current_username: export_applications(current_user), 
                            bootstyle=SUCCESS)
    export_btn.pack(side='left', padx=5)

    # Update history table
    update_history_table(history_table, username)

# Main function
def main():
    global root
    root = ttk.Window(themename="superhero")
    root.title("Job Application Tracker")
    root.geometry("400x300")
    root.withdraw()  # Hide the main root window initially

    # Show Login/Register Window initially
    show_login_register_window(is_register=False)

    root.mainloop()

# Run the application
if __name__ == "__main__":
    main()