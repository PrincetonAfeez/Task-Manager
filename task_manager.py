import json                                         # Library to read/write JSON files for data persistence
import os                                           # Library to interact with the operating system (file checks)
import csv                                          # Library to handle CSV generation for spreadsheet exports
import hashlib                                      # Library to transform passwords into secure, non-readable hashes
from datetime import datetime                       # Library to handle system time and date formatting

# --- CONFIGURATION ---
DATA_FILE = "tasks.json"                            # Primary file for storing user tasks
USER_FILE = "users.json"                            # Secure file for storing hashed credentials
ARCHIVE_FILE = "archive.json"                       # File for storing "completed" tasks moved out of main view

# --- TERMINAL COLORS (ANSI ESCAPE CODES) ---
class Colors:
    HEADER = '\033[95m'                             # Purple: Used for main table borders
    BLUE = '\033[94m'                               # Blue: Used for titles and success messages
    GREEN = '\033[92m'                              # Green: Indicates 'Done' or positive results
    YELLOW = '\033[93m'                             # Yellow: Indicates 'Medium' priority or warnings
    RED = '\033[91m'                                # Red: Indicates 'High' priority, Overdue, or Errors
    CYAN = '\033[96m'                               # Cyan: Indicates 'Low' priority or neutral info
    ENDC = '\033[0m'                                # Reset: Vital to stop color bleed after a string
    BOLD = '\033[1m'                                # Bold: Enhances visibility for headers

# --- SECURITY & AUTHENTICATION ---
def hash_password(password):
    """Encodes a string into a SHA-256 hex digest for security."""
    return hashlib.sha256(password.encode()).hexdigest() # Returns a 64-character secure string

def setup_account():
    """Initializes the admin account if the user file is missing."""
    if not os.path.exists(USER_FILE):               # Only trigger on the very first run
        print(f"{Colors.BOLD}{Colors.CYAN}--- INITIAL SECURITY SETUP ---{Colors.ENDC}")
        username = get_non_empty_input("Create Admin Username: ") # Force non-blank input
        password = get_non_empty_input("Create Admin Password: ") # Force non-blank input
        print(f"\n{Colors.YELLOW}Set a Recovery Question (to reset if forgotten){Colors.ENDC}")
        question = get_non_empty_input("Question (e.g., Favorite City): ") # Reset hint
        answer = get_non_empty_input("Answer: ")                  # Proof of ownership
        
        user_data = {
            "username": username,
            "password": hash_password(password),    # Never store raw passwords
            "recovery_question": question,
            "recovery_answer": hash_password(answer.lower()) # Store answer hash (case-insensitive)
        }
        with open(USER_FILE, "w") as f:             # Write the JSON user profile
            json.dump(user_data, f, indent=4)
        print(f"{Colors.GREEN}Account created successfully!{Colors.ENDC}\n")

def reset_password():
    """Validates the recovery question to allow password modification."""
    if not os.path.exists(USER_FILE): return False  # Safety check
    with open(USER_FILE, "r") as f:
        data = json.load(f)                         # Load current user data
    print(f"\n{Colors.BOLD}--- PASSWORD RECOVERY ---{Colors.ENDC}")
    print(f"Question: {data['recovery_question']}")
    ans_input = input("Your Answer: ").strip().lower() # Prompt for the secret answer
    if hash_password(ans_input) == data['recovery_answer']: # Compare hashes
        new_p = get_non_empty_input("Enter New Password: ") # Get new pass if matched
        data['password'] = hash_password(new_p)     # Update the hash
        with open(USER_FILE, "w") as f:
            json.dump(data, f, indent=4)            # Save back to file
        print(f"{Colors.GREEN}Password updated! You may now login.{Colors.ENDC}")
        return True                                 # Success flag
    print(f"{Colors.RED}Incorrect answer. Recovery failed.{Colors.ENDC}")
    return False                                    # Failure flag

def login():
    """The gateway function that protects the app on startup."""
    setup_account()                                 # Run first-time setup if needed
    with open(USER_FILE, "r") as f:
        stored = json.load(f)                       # Retrieve the credentials
    attempts = 3                                    # User gets 3 tries
    while attempts > 0:
        print(f"\n{Colors.BOLD}Login Required ({attempts} tries left){Colors.ENDC}")
        print("Tip: Type 'forgot' for recovery or 'exit' to quit.")
        u_input = input("Username: ").strip()       # Get username input
        if u_input.lower() == 'exit': exit()        # Allow clean exit from login screen
        if u_input.lower() == 'forgot':             # Trigger recovery flow
            if reset_password(): attempts = 3; continue # Reset tries if password fixed
            else: attempts -= 1; continue           # Penalize on failed recovery
        p_input = input("Password: ").strip()       # Get password input
        if u_input == stored["username"] and hash_password(p_input) == stored["password"]:
            print(f"{Colors.GREEN}Access Granted. Welcome, {u_input}!{Colors.ENDC}")
            return True                             # Unlock the main app
        attempts -= 1                               # Deduct attempt on mismatch
        print(f"{Colors.RED}Invalid credentials.{Colors.ENDC}")
    print(f"{Colors.RED}System Locked for security.{Colors.ENDC}")
    return False                                    # Fail and exit app

# --- STORAGE ENGINE ---
def load_tasks():
    """Reads tasks from JSON and returns them as a Python list."""
    if not os.path.exists(DATA_FILE): return []     # Return empty list if no file
    with open(DATA_FILE, "r") as file:
        try: return json.load(file)                 # Parse JSON to Python list
        except json.JSONDecodeError: return []      # Return empty if file is corrupt

def save_tasks(tasks):
    """Writes the current task list into the JSON file with pretty-print."""
    with open(DATA_FILE, "w") as file:
        json.dump(tasks, file, indent=4)            # Save with 4-space indentation

# --- CORE LOGIC (CRUD & DASHBOARD) ---
def add_task(description, priority="Medium", due_date="None"):
    """Appends a new task dictionary to the master database."""
    tasks = load_tasks()                            # Load current state
    new_task = {
        "id": max([t["id"] for t in tasks], default=0) + 1, # Logic to find next unique ID
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "status": False,                            # New tasks are never 'Done' by default
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Metadata
    }
    tasks.append(new_task)                          # Add to local list
    save_tasks(tasks)                               # Commit to file
    print(f"{Colors.GREEN}✔ Task added successfully!{Colors.ENDC}")

def display_task_table(tasks_list):
    """A reusable UI engine to print data in a color-coded table format."""
    if not tasks_list:                              # UX: Don't print empty tables
        print(f"\n{Colors.YELLOW}--- No tasks to display ---{Colors.ENDC}")
        return
    print("\n" + Colors.BOLD + Colors.HEADER + "="*95 + Colors.ENDC)
    print(f"{Colors.BOLD}{'ID':<4} | {'Description':<25} | {'Priority':<10} | {'Due':<12} | {'Status':<10}{Colors.ENDC}")
    print("-" * 95)                                 # Separator line
    for t in tasks_list:                            # Iterate and colorize
        p_val = t.get("priority", "Medium")
        # Inline conditional for color selection
        p_col = Colors.RED if p_val == "High" else Colors.YELLOW if p_val == "Medium" else Colors.CYAN
        s_txt = f"{Colors.GREEN}Done{Colors.ENDC}" if t["status"] else f"{Colors.RED}Pending{Colors.ENDC}"
        print(f"{t['id']:<4} | {t['description']:<25} | {p_col}{p_val:<10}{Colors.ENDC} | {t['due_date']:<12} | {s_txt:<10}")
    print(Colors.BOLD + Colors.HEADER + "="*95 + Colors.ENDC + "\n")

def search_tasks(keyword):
    """Filters tasks based on a search term within the description."""
    tasks = load_tasks()
    # List comprehension to find matches (case-insensitive)
    results = [t for t in tasks if keyword.lower() in t["description"].lower()]
    display_task_table(results)                     # Display the filtered subset

def view_tasks_sorted(sort_by):
    """Orders tasks based on priority weight, due date, or creation ID."""
    tasks = load_tasks()
    if not tasks: return
    p_map = {"High": 1, "Medium": 2, "Low": 3, "None": 4} # Sorting priority map
    if sort_by == "priority": tasks.sort(key=lambda x: p_map.get(x["priority"], 2))
    elif sort_by == "due_date": tasks.sort(key=lambda x: (x["due_date"] == "None", x["due_date"]))
    else: tasks.sort(key=lambda x: x["id"])         # Default sort by ID
    display_task_table(tasks)                       # Show the sorted list

def mark_done(task_id):
    """Updates a task's status to True based on user-provided ID."""
    tasks = load_tasks()
    found = False
    for t in tasks:
        if t["id"] == task_id:                      # Target the specific ID
            t["status"] = True                      # Flip the bit to True
            found = True; break                     # Stop loop early for efficiency
    if found: save_tasks(tasks); print(f"{Colors.GREEN}✔ Task #{task_id} completed!{Colors.ENDC}")
    else: print(f"{Colors.RED}✖ Task ID not found.{Colors.ENDC}")

def delete_task(task_id):
    """Removes a task entry permanently from the main database."""
    tasks = load_tasks()
    # Filter the list keeping everything EXCEPT the targeted ID
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) < len(tasks):                 # If length changed, deletion worked
        save_tasks(new_tasks)
        print(f"{Colors.CYAN}🗑 Task #{task_id} deleted.{Colors.ENDC}")
    else: print(f"{Colors.RED}✖ Task ID not found.{Colors.ENDC}")

def export_to_csv():
    """Generates a comma-separated file readable by Excel or Google Sheets."""
    tasks = load_tasks()
    if not tasks: print(f"{Colors.RED}Nothing to export!{Colors.ENDC}"); return
    filename = "task_export.csv"
    with open(filename, "w", newline="") as f:      # Write-mode for CSV
        writer = csv.DictWriter(f, fieldnames=tasks[0].keys()) # Map dict keys to CSV headers
        writer.writeheader(); writer.writerows(tasks) # Write schema and then data
    print(f"{Colors.CYAN}✅ Exported to {filename}{Colors.ENDC}")

def check_deadlines():
    """Logic to scan tasks and print immediate alerts upon application startup."""
    tasks = load_tasks(); now = datetime.now()
    overdue, soon = [], []                          # Buckets for filtering
    for t in tasks:
        if t["due_date"] != "None" and not t["status"]:
            try:
                due = datetime.strptime(t["due_date"], "%Y-%m-%d")
                if due < now: overdue.append(t["description"]) # Past the date
                elif (due - now).days <= 1: soon.append(t["description"]) # Within 24 hours
            except ValueError: continue             # Skip tasks with bad date formatting
    if overdue: print(f"{Colors.RED}{Colors.BOLD}⚠️ OVERDUE: {', '.join(overdue)}{Colors.ENDC}")
    if soon: print(f"{Colors.YELLOW}{Colors.BOLD}🔔 DUE SOON (24h): {', '.join(soon)}{Colors.ENDC}")

def show_stats():
    """Visual dashboard for productivity metrics and progress tracking."""
    tasks = load_tasks()
    if not tasks: print("No tasks for stats."); return
    total = len(tasks)                              # Total count
    done = len([t for t in tasks if t["status"]])   # Completed count
    percent = (done / total) * 100                  # Success percentage
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- STATS DASHBOARD ---{Colors.ENDC}")
    print(f"Total: {total} | Completed: {done} | Rate: {percent:.1f}%")
    bar = "█" * int(percent // 5) + "-" * (20 - int(percent // 5)) # ASCII Bar calculation
    print(f"Progress: [{Colors.GREEN}{bar}{Colors.ENDC}]")

def archive_tasks():
    """Moves 'Done' tasks to a separate JSON file to keep main database fast."""
    tasks = load_tasks()
    done = [t for t in tasks if t["status"]]        # Items to move
    active = [t for t in tasks if not t["status"]]  # Items to keep
    if not done: print(f"{Colors.YELLOW}No tasks to archive.{Colors.ENDC}"); return
    old_archive = []
    if os.path.exists(ARCHIVE_FILE):                # Check if archive exists
        with open(ARCHIVE_FILE, "r") as f:
            try: old_archive = json.load(f)
            except: pass
    old_archive.extend(done)                        # Merge new archives with old
    with open(ARCHIVE_FILE, "w") as f: json.dump(old_archive, f, indent=4)
    save_tasks(active)                              # Clear main list of completed items
    print(f"{Colors.CYAN}✅ {len(done)} tasks archived.{Colors.ENDC}")

# --- VALIDATION UTILITIES ---
def get_non_empty_input(prompt):
    """Looping prompt that rejects blank or whitespace-only strings."""
    while True:
        v = input(prompt).strip()
        if v: return v                              # Return only if data exists
        print(f"{Colors.RED}✖ Cannot be empty.{Colors.ENDC}")

def get_valid_date(prompt):
    """Forces user to input YYYY-MM-DD or hit enter for None."""
    while True:
        v = input(prompt).strip()
        if not v: return "None"                     # Optional field
        try:
            datetime.strptime(v, "%Y-%m-%d")        # Validation attempt
            return v
        except ValueError: print(f"{Colors.RED}✖ Use YYYY-MM-DD.{Colors.ENDC}")

def get_valid_priority():
    """Provides a selection menu for priority to prevent typos."""
    opts = {"1": "High", "2": "Medium", "3": "Low"}
    while True:
        print(f"{Colors.CYAN}Priority: (1) High (2) Medium (3) Low{Colors.ENDC}")
        c = input("Select 1-3 [Default 2]: ").strip()
        if not c: return "Medium"                   # Default fallback
        if c in opts: return opts[c]                # Match selection
        print(f"{Colors.RED}✖ Invalid Choice.{Colors.ENDC}")

def bulk_action(action_type):
    """Performs an action (done/delete) on multiple IDs at once."""
    raw_ids = input("Enter Task IDs separated by commas (e.g. 1, 4, 7): ")
    try:
        # Convert "1, 2, 3" into [1, 2, 3]
        target_ids = [int(i.strip()) for i in raw_ids.split(",")]
        for t_id in target_ids:
            if action_type == "done":
                mark_done(t_id)
            elif action_type == "delete":
                delete_task(t_id)
    except ValueError:
        print(f"{Colors.RED}✖ Error: Please use numbers and commas only.{Colors.ENDC}")

def toggle_timer(task_id):
    """Starts or stops a timer for a specific task."""
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # If timer isn't running, start it
            if t.get("timer_running") is None or t["timer_running"] == False:
                t["timer_running"] = True
                t["start_time"] = now
                print(f"{Colors.GREEN}▶ Timer started for Task #{task_id}{Colors.ENDC}")
            else:
                # Calculate elapsed time
                start = datetime.strptime(t["start_time"], "%Y-%m-%d %H:%M:%S")
                elapsed = (datetime.now() - start).total_seconds() / 60
                t["total_minutes"] = t.get("total_minutes", 0) + elapsed
                t["timer_running"] = False
                print(f"{Colors.YELLOW}■ Timer stopped. Added {elapsed:.1f} mins.{Colors.ENDC}")
            save_tasks(tasks)
            return
    print(f"{Colors.RED}✖ Task not found.{Colors.ENDC}")
    
# --- MAIN CONTROLLER ---
def main():
    """The master loop that keeps the application alive and interactive."""
    check_deadlines()                               # Auto-run alert engine on login
    while True:
        print(f"\n{Colors.BOLD}{Colors.BLUE}--- TASK MANAGER PRO V2.0 ---{Colors.ENDC}")
        print("1. View Tasks")                      # Read
        print("2. Add Task")                        # Create
        print("3. Mark Task Done")                  # Update
        print("4. Delete Task")                     # Delete
        print("5. Search Tasks")                    # Filter
        print("6. Sort Tasks")                      # Reorder
        print("7. Export to CSV")                   # Export
        print("8. Productivity Stats")              # Analytics
        print("9. Archive Completed")               # Maintenance
        print("10. Exit")                           # Termination
        
        choice = input("\nSelect (1-10): ").strip()
        
        if choice == "1": display_task_table(load_tasks())
        elif choice == "2":
            d = get_non_empty_input("Description: ")
            p = get_valid_priority()
            dt = get_valid_date("Due Date (YYYY-MM-DD) or [Enter]: ")
            add_task(d, p, dt)
        elif choice == "3":
            try: mark_done(int(input("Task ID: ")))
            except ValueError: print(f"{Colors.RED}✖ Enter a numeric ID.{Colors.ENDC}")
        elif choice == "4":
            try: delete_task(int(input("Task ID: ")))
            except ValueError: print(f"{Colors.RED}✖ Enter a numeric ID.{Colors.ENDC}")
        elif choice == "5": search_tasks(input("Keyword: "))
        elif choice == "6":
            print("\nSort by: (1) Priority (2) Due Date (3) ID")
            s_map = {"1": "priority", "2": "due_date", "3": "id"}
            view_tasks_sorted(s_map.get(input("Choice: "), "id"))
        elif choice == "7": export_to_csv()
        elif choice == "8": show_stats()
        elif choice == "9": archive_tasks()
        elif choice == "10": print(f"{Colors.CYAN}Goodbye!{Colors.ENDC}"); break
        else: print(f"{Colors.RED}✖ Invalid choice (1-10).{Colors.ENDC}")

if __name__ == "__main__":
    if login(): main()                              # Only start app if login returns True
    else: exit()                                    # Otherwise terminate