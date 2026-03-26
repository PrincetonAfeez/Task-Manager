import json                                         # Library to read/write JSON files
import os                                           # Library to check if files exist on the system
import csv                                          # Library to export data to spreadsheet format
from datetime import datetime                       # Library to handle dates and timestamps
import hashlib                                      # Library to securely hash passwords

# --- CONFIGURATION ---
DATA_FILE = "tasks.json"                            # The filename for our local JSON database
USER_FILE = "users.json"                            # New file for credentials

# --- TERMINAL COLORS (ANSI ESCAPE CODES) ---
class Colors:
    HEADER = '\033[95m'                             # Purple/Magenta for headers
    BLUE = '\033[94m'                               # Blue for titles
    GREEN = '\033[92m'                              # Green for 'Completed' status
    YELLOW = '\033[93m'                             # Yellow for 'Medium' priority
    RED = '\033[91m'                                # Red for 'High' priority or Errors
    CYAN = '\033[96m'                               # Cyan for 'Low' priority or Info
    ENDC = '\033[0m'                                # Reset code to return to default text color
    BOLD = '\033[1m'                                # Bold text modifier

# --- STORAGE ENGINE ---
def load_tasks():                                   # Loads data from JSON to Python List
    if not os.path.exists(DATA_FILE):               # If the file is missing...
        return []                                   # Return an empty list to avoid errors
    with open(DATA_FILE, "r") as file:              # Open file in read mode
        try:                                        # Try block to handle empty/broken files
            return json.load(file)                  # Convert JSON string to Python list
        except json.JSONDecodeError:                # If file is corrupted...
            return []                               # Return empty list

def hash_password(password):
    """Converts a plain-text password into a secure SHA-256 hash."""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_account():
    """Creates the initial admin account with a recovery question."""
    if not os.path.exists(USER_FILE):
        print(f"{Colors.CYAN}--- Initial Security Setup ---{Colors.ENDC}")
        username = get_non_empty_input("Create Admin Username: ")
        password = get_non_empty_input("Create Admin Password: ")
        print(f"\n{Colors.YELLOW}Set a Recovery Question (in case you forget your password){Colors.ENDC}")
        question = get_non_empty_input("Recovery Question (e.g., Mother's maiden name): ")
        answer = get_non_empty_input("Recovery Answer: ")
        
        user_data = {
            "username": username,
            "password": hash_password(password),
            "recovery_question": question,
            "recovery_answer": hash_password(answer.lower()) # Hash the answer too!
        }
        with open(USER_FILE, "w") as f:
            json.dump(user_data, f)
        print(f"{Colors.GREEN}Account created successfully!{Colors.ENDC}\n")

def reset_password():
    """Flow to reset password using the recovery question."""
    if not os.path.exists(USER_FILE):
        return
    
    with open(USER_FILE, "r") as f:
        data = json.load(f)

    print(f"\n{Colors.BOLD}--- Password Recovery ---{Colors.ENDC}")
    print(f"Question: {data['recovery_question']}")
    ans_input = input("Your Answer: ").strip().lower()

    if hash_password(ans_input) == data['recovery_answer']:
        new_pass = get_non_empty_input("Enter New Password: ")
        data['password'] = hash_password(new_pass)
        with open(USER_FILE, "w") as f:
            json.dump(data, f)
        print(f"{Colors.GREEN}Password updated! Please login again.{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.RED}Incorrect answer. Recovery failed.{Colors.ENDC}")
        return False

def login():
    """Login gateway with a 'Forgot Password' option."""
    setup_account()
    
    with open(USER_FILE, "r") as f:
        stored_user = json.load(f)

    attempts = 3
    while attempts > 0:
        print(f"\n{Colors.BOLD}Login Required ({attempts} attempts left){Colors.ENDC}")
        print("Type 'forgot' if you lost your password.")
        user_input = input("Username: ").strip()
        
        if user_input.lower() == 'forgot':
            if reset_password():
                attempts = 3 # Reset attempts if they successfully changed password
                continue
            else:
                attempts -= 1
                continue

        pass_input = input("Password: ").strip()

        if user_input == stored_user["username"] and hash_password(pass_input) == stored_user["password"]:
            print(f"{Colors.GREEN}Access Granted. Welcome, {user_input}!{Colors.ENDC}")
            return True
        else:
            attempts -= 1
            print(f"{Colors.RED}Invalid credentials.{Colors.ENDC}")
    
    print(f"{Colors.RED}System Locked.{Colors.ENDC}")
    return False

def save_tasks(tasks):                              # Saves Python List to JSON file
    with open(DATA_FILE, "w") as file:              # Open file in write mode (overwrites old data)
        json.dump(tasks, file, indent=4)            # Save with 4-space indent for readability

# --- CORE LOGIC (CRUD & FEATURES) ---
def add_task(description, priority="Medium", due_date="None"): 
    tasks = load_tasks()                            # Get existing tasks
    new_task = {                                    # Create a dictionary for the new entry
        "id": len(tasks) + 1,                       # Auto-increment ID based on list length
        "description": description,                 # User's task text
        "priority": priority,                       # User's priority choice
        "due_date": due_date,                       # User's date string
        "status": False,                            # Default to 'Pending' (False)
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Timestamp
    }
    tasks.append(new_task)                          # Add new task to the list
    save_tasks(tasks)                               # Save to disk
    print(f"{Colors.GREEN}✔ Task added successfully!{Colors.ENDC}")

def export_to_csv():                                # Converts JSON to Excel-friendly CSV
    tasks = load_tasks()                            # Get data
    if not tasks:                                   # Check if empty
        print(f"{Colors.RED}✖ Nothing to export!{Colors.ENDC}")
        return
    filename = "task_export.csv"                    # Target filename
    headers = tasks[0].keys()                       # Use dictionary keys as CSV headers
    with open(filename, "w", newline="") as f:      # Open CSV file
        writer = csv.DictWriter(f, fieldnames=headers) # Setup CSV writer
        writer.writeheader()                        # Write the top header row
        writer.writerows(tasks)                     # Write all task rows
    print(f"{Colors.CYAN}✅ Exported to {filename}{Colors.ENDC}")

def display_task_table(tasks_list):                 # Universal function to print the UI table
    if not tasks_list:                              # If list is empty...
        print(f"\n{Colors.YELLOW}--- No tasks to display ---{Colors.ENDC}")
        return
    print("\n" + Colors.BOLD + Colors.HEADER + "="*95 + Colors.ENDC) # Top border
    print(f"{Colors.BOLD}{'ID':<4} | {'Description':<20} | {'Priority':<10} | {'Due':<12} | {'Status':<10}{Colors.ENDC}")
    print("-" * 95)                                 # Header separator
    for t in tasks_list:                            # Loop through tasks
        p_val = t.get("priority", "Medium")         # Get priority
        # Pick color based on priority string
        p_col = Colors.RED if p_val == "High" else Colors.YELLOW if p_val == "Medium" else Colors.CYAN
        # Pick text/color based on status boolean
        s_txt = f"{Colors.GREEN}Done{Colors.ENDC}" if t["status"] else f"{Colors.RED}Pending{Colors.ENDC}"
        # Print formatted row
        print(f"{t['id']:<4} | {t['description']:<20} | {p_col}{p_val:<10}{Colors.ENDC} | {t['due_date']:<12} | {s_txt:<10}")
    print(Colors.BOLD + Colors.HEADER + "="*95 + Colors.ENDC + "\n") # Bottom border

def view_tasks():                                   # Main view function
    tasks = load_tasks()                            # Load data
    display_task_table(tasks)                       # Send to table displayer

def mark_done(task_id):                             # Update status function
    tasks = load_tasks()                            # Load data
    found = False                                   # Search flag
    for task in tasks:                              # Iterate
        if task["id"] == task_id:                   # Match ID
            task["status"] = True                   # Set to True
            found = True                            # Mark found
            break                                   # Stop searching
    if found:
        save_tasks(tasks)                           # Save changes
        print(f"{Colors.GREEN}✔ Task #{task_id} completed!{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✖ Task ID not found.{Colors.ENDC}")

def delete_task(task_id):                           # Delete function
    tasks = load_tasks()                            # Load data
    # Filter list: Keep all tasks EXCEPT the one matching the ID
    updated = [t for t in tasks if t["id"] != task_id] 
    if len(updated) < len(tasks):                   # If length changed, deletion happened
        save_tasks(updated)                         # Save
        print(f"{Colors.CYAN}🗑 Task #{task_id} deleted.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✖ Task ID not found.{Colors.ENDC}")

def search_tasks(keyword):                          # Search function
    tasks = load_tasks()                            # Load data
    # Case-insensitive search inside descriptions
    results = [t for t in tasks if keyword.lower() in t["description"].lower()]
    display_task_table(results)                     # Display results

def view_tasks_sorted(sort_by="id"):                # Sorting function
    tasks = load_tasks()                            # Load data
    if not tasks: return                            # Exit if empty
    p_order = {"High": 1, "Medium": 2, "Low": 3, "None": 4} # Numeric map for priorities
    if sort_by == "priority":                       # Sort by importance
        tasks.sort(key=lambda x: p_order.get(x.get("priority", "Medium"), 2))
    elif sort_by == "due_date":                     # Sort by date string
        tasks.sort(key=lambda x: (x["due_date"] == "None", x["due_date"]))
    else:                                           # Sort by ID (default)
        tasks.sort(key=lambda x: x["id"])
    display_task_table(tasks)                       # Display sorted list

# --- VALIDATION HELPERS ---
def get_non_empty_input(prompt):                    # Forces user to type something
    while True:                                     # Loop until valid
        val = input(prompt).strip()                 # Get input and remove extra spaces
        if val: return val                          # If not blank, return it
        print(f"{Colors.RED}✖ Input cannot be empty.{Colors.ENDC}")

def get_valid_date(prompt):                         # Ensures date is real/formatted
    while True:                                     # Loop until valid
        val = input(prompt).strip()                 # Get input
        if not val: return "None"                   # Allow empty input for "None"
        try:
            datetime.strptime(val, "%Y-%m-%d")      # Validate YYYY-MM-DD
            return val                              # Return if valid
        except ValueError:                          # If format is wrong...
            print(f"{Colors.RED}✖ Use YYYY-MM-DD format.{Colors.ENDC}")

def get_valid_priority():                           # Restricts priority options
    opts = {"1": "High", "2": "Medium", "3": "Low"} # Map numbers to words
    while True:                                     # Loop until valid
        print(f"{Colors.CYAN}Priority: (1) High (2) Medium (3) Low{Colors.ENDC}")
        choice = input("Select 1-3 [Default 2]: ").strip()
        if not choice: return "Medium"              # Default if empty
        if choice in opts: return opts[choice]      # Return mapped word
        print(f"{Colors.RED}✖ Invalid selection.{Colors.ENDC}")

def check_deadlines():
    """Automatically alerts the user about overdue or upcoming tasks."""
    tasks = load_tasks()
    now = datetime.now()
    overdue = []
    upcoming = []

    for t in tasks:
        if t["due_date"] != "None" and not t["status"]:
            try:
                due = datetime.strptime(t["due_date"], "%Y-%m-%d")
                if due < now:
                    overdue.append(t["description"])
                elif (due - now).days <= 1: # Due within 24 hours
                    upcoming.append(t["description"])
            except ValueError:
                continue

    if overdue:
        print(f"{Colors.RED}{Colors.BOLD}⚠️ OVERDUE TASKS: {', '.join(overdue)}{Colors.ENDC}")
    if upcoming:
        print(f"{Colors.YELLOW}{Colors.BOLD}🔔 DUE SOON (24h): {', '.join(upcoming)}{Colors.ENDC}")

def show_stats():
    """Calculates and displays productivity analytics."""
    tasks = load_tasks()
    if not tasks:
        print("No data for statistics.")
        return
    
    total = len(tasks)
    done = len([t for t in tasks if t["status"]])
    pending = total - done
    percent = (done / total) * 100
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- PRODUCTIVITY DASHBOARD ---{Colors.ENDC}")
    print(f"Total Tasks: {total}")
    print(f"Completed:  {Colors.GREEN}{done}{Colors.ENDC}")
    print(f"Pending:    {Colors.RED}{pending}{Colors.ENDC}")
    print(f"Success Rate: {percent:.1f}%")
    
    # Simple ASCII Bar Chart
    bar_length = 20
    filled = int(bar_length * done // total)
    bar = "█" * filled + "-" * (bar_length - filled)
    print(f"Progress: [{Colors.GREEN}{bar}{Colors.ENDC}]")

def archive_tasks():
    """Moves completed tasks to a separate archive file to declutter."""
    tasks = load_tasks()
    completed = [t for t in tasks if t["status"]]
    active = [t for t in tasks if not t["status"]]

    if not completed:
        print(f"{Colors.YELLOW}No completed tasks to archive.{Colors.ENDC}")
        return

    archive_file = "archive.json"
    existing_archive = []
    if os.path.exists(archive_file):
        with open(archive_file, "r") as f:
            try: existing_archive = json.load(f)
            except: pass
    
    existing_archive.extend(completed)
    
    with open(archive_file, "w") as f:
        json.dump(existing_archive, f, indent=4)
    
    save_tasks(active) # Save only the pending tasks back to the main file
    print(f"{Colors.CYAN}✅ {len(completed)} tasks moved to archive.json!{Colors.ENDC}")

# --- MAIN INTERFACE ---
def main():                                         # Main Program Loop
    check_deadlines()  # <--- Triggers automatically on startup!
    while True:                                     # Keep app running
        print(f"\n{Colors.BOLD}{Colors.BLUE}--- TASK MANAGER PRO V1.0 ---{Colors.ENDC}")
        print("1. View Tasks")                      # Option 1
        print("2. Add Task")                       # Option 2
        print("3. Mark Task Done")                  # Option 3
        print("4. Delete Task")                     # Option 4
        print("5. Search Tasks")                    # Option 5
        print("6. Export to CSV")                   # Option 6 (Fixed numbering!)
        print("7. Sort & View Tasks")               # Option 7
        print("8. Productivity Stats")
        print("9. Archive Completed Tasks")
        print("10. Exit")
        
        choice = input("\nSelect (1-10): ")          # User selection
        
        if choice == "1": view_tasks()              # Standard View
        elif choice == "2":                         # Add Logic
            d = get_non_empty_input("Description: ")
            p = get_valid_priority()
            dt = get_valid_date("Due Date (YYYY-MM-DD) or [Enter]: ")
            add_task(d, p, dt)
        elif choice == "3":                         # Done Logic
            try:
                i = int(input("Task ID: "))
                mark_done(i)
            except ValueError: print(f"{Colors.RED}✖ Enter a number.{Colors.ENDC}")
        elif choice == "4":                         # Delete Logic
            try:
                i = int(input("Task ID to delete: "))
                delete_task(i)
            except ValueError: print(f"{Colors.RED}✖ Enter a number.{Colors.ENDC}")
        elif choice == "5":                         # Search Logic
            q = input("Keyword: ")
            search_tasks(q)
        elif choice == "6": export_to_csv()          # CSV Logic
        elif choice == "7":                         # Sort Logic
            print("\nSort by: (1) Priority (2) Due Date (3) ID")
            sc = input("Choice: ")
            s_map = {"1": "priority", "2": "due_date", "3": "id"}
            view_tasks_sorted(s_map.get(sc, "id"))
        elif choice == "8":
            show_stats()
        elif choice == "9":
            archive_tasks()
        elif choice == "10":                         # Exit Logic
            print(f"{Colors.BLUE}Goodbye!{Colors.ENDC}")
            break                                   # Kill loop
        else: print(f"{Colors.RED}✖ Invalid choice.{Colors.ENDC}")

if __name__ == "__main__":
    # The app now starts with a login check
    if login():
        main()
    else:
        # If login fails 3 times, the script just ends
        exit()