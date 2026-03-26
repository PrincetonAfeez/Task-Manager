import json                                         # Library to read/write JSON files for data persistence
import os                                           # Library to interact with the operating system (file checks)
import csv                                          # Library to handle CSV generation for spreadsheet exports
import hashlib                                      # Library to transform passwords into secure, non-readable hashes
from datetime import datetime, timedelta            # Library to handle system time, date formatting, and math

# --- CONFIGURATION ---
DATA_FILE = "tasks.json"                            # Primary file for storing user tasks
USER_FILE = "users.json"                            # Secure file for storing hashed credentials and player stats
ARCHIVE_FILE = "archive.json"                       # File for storing completed tasks moved out of main view

# --- TERMINAL COLORS (ANSI ESCAPE CODES) ---
class Colors:
    HEADER = '\033[95m'                             # Purple: Used for main table borders
    BLUE = '\033[94m'                               # Blue: Used for titles and success messages
    GREEN = '\033[92m'                              # Green: Indicates 'Done' or positive results
    YELLOW = '\033[93m'                             # Yellow: Indicates 'Medium' priority or warnings
    RED = '\033[91m'                                # Red: Indicates 'High' priority or Errors
    CYAN = '\033[96m'                               # Cyan: Indicates 'Low' priority or neutral info
    GOLD = '\033[33m'                               # Gold: Used for Leveling and XP rewards
    FLASH = '\033[5m'                               # Flash: Makes text blink (used for Escalated tasks)
    BOLD = '\033[1m'                                # Bold: Enhances visibility for headers
    ENDC = '\033[0m'                                # Reset: Vital to stop color bleed

# --- SECURITY & AUTHENTICATION ---
def hash_password(password):
    """Encodes a string into a SHA-256 hex digest for security."""
    return hashlib.sha256(password.encode()).hexdigest() # Returns a 64-character secure string

def setup_account():
    """Initializes the admin account and player stats if missing."""
    if not os.path.exists(USER_FILE):               # Only trigger on the very first run
        print(f"{Colors.BOLD}{Colors.CYAN}--- INITIAL SECURITY & PLAYER SETUP ---{Colors.ENDC}")
        u = get_non_empty_input("Create Admin Username: ") # Force non-blank input
        p = get_non_empty_input("Create Admin Password: ") # Force non-blank input
        q = get_non_empty_input("Recovery Question (e.g. First Pet): ") # Recovery hint
        a = get_non_empty_input("Answer: ")                  # Proof of ownership
        user_data = {
            "username": u, "password": hash_password(p), 
            "q": q, "a": hash_password(a.lower()),  # Store answer hash (case-insensitive)
            "xp": 0, "level": 1                     # Initialize Gamification stats
        }
        with open(USER_FILE, "w") as f: json.dump(user_data, f, indent=4) # Write JSON profile
        print(f"{Colors.GREEN}Account and Player Profile created!{Colors.ENDC}\n")

def login():
    """The gateway function that protects the app and manages recovery."""
    setup_account()                                 # Run first-time setup if needed
    with open(USER_FILE, "r") as f: user = json.load(f) # Retrieve credentials and stats
    for i in range(3, 0, -1):                       # User gets 3 attempts
        print(f"\n{Colors.BOLD}Login Required ({i} tries left). Type 'forgot' for recovery.{Colors.ENDC}")
        u_input = input("Username: ").strip()       # Get username
        if u_input.lower() == 'exit': exit()        # Allow clean exit
        if u_input.lower() == 'forgot':             # Recovery flow
            print(f"Question: {user['q']}")         # Show the hint
            if hash_password(input("Answer: ").lower()) == user['a']: # Check answer hash
                user['password'] = hash_password(get_non_empty_input("New Password: ")) # Update pass
                with open(USER_FILE, "w") as f: json.dump(user, f, indent=4) # Save update
                print(f"{Colors.GREEN}Password Reset!{Colors.ENDC}"); continue # Restart loop
        p_input = input("Password: ").strip()       # Get password
        if u_input == user["username"] and hash_password(p_input) == user["password"]:
            print(f"{Colors.GREEN}Access Granted! [Lvl {user.get('level', 1)}]{Colors.ENDC}")
            return True                             # Unlock the app
    return False                                    # Fail after 3 tries

# --- STORAGE ENGINE ---
def load_tasks():
    """Reads tasks from JSON; returns empty list if file is missing or broken."""
    if not os.path.exists(DATA_FILE): return []     
    with open(DATA_FILE, "r") as f:
        try: return json.load(f)                 
        except: return []                           

def save_tasks(tasks):
    """Writes the task list to JSON with 4-space indentation."""
    with open(DATA_FILE, "w") as f: json.dump(tasks, f, indent=4)            

# --- CORE LOGIC & FEATURES ---
def add_task(desc, pri, due, cat):
    """Creates a task with metadata, categories, and optional dependencies."""
    tasks = load_tasks()                            # Load existing data
    print("Is this blocked by another task? (Enter ID or press Enter for none)")
    dep = input("Blocked by ID: ").strip()          # Dependency tracking
    new_task = {
        "id": max([t["id"] for t in tasks], default=0) + 1, # Generate unique ID
        "description": desc, "priority": pri, "due_date": due, "category": cat,
        "status": False, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_minutes": 0, "timer_running": False, # Initialize time tracking
        "blocked_by": int(dep) if dep.isdigit() else None # Link to another task
    }
    tasks.append(new_task)                          # Add to list
    save_tasks(tasks)                               # Commit to disk
    print(f"{Colors.GREEN}✔ Task added to [{cat}]!{Colors.ENDC}")

def mark_done(task_id):
    """Updates status, enforces dependencies, and awards XP."""
    tasks = load_tasks()                            # Load database
    for t in tasks:
        if t["id"] == task_id:                      # Find target task
            if t.get("blocked_by"):                 # Check for blockers
                blocker = next((x for x in tasks if x["id"] == t["blocked_by"]), None)
                if blocker and not blocker["status"]: # Blocker must be 'Done'
                    print(f"{Colors.RED}✖ BLOCKED: Finish Task #{t['blocked_by']} first!{Colors.ENDC}")
                    return
            if not t["status"]:                     # If not already done
                t["status"] = True                  # Mark complete
                save_tasks(tasks)                   # Save change
                award_xp(t["priority"])             # Trigger Gamification
                print(f"{Colors.GREEN}✔ Task #{task_id} marked Done!{Colors.ENDC}")
                return
    print(f"{Colors.RED}✖ Task ID not found.{Colors.ENDC}")

def award_xp(priority):
    """Calculates XP based on difficulty and handles player Level Ups."""
    gain = {"High": 50, "Medium": 20, "Low": 10}.get(priority, 10) # Difficulty mapping
    with open(USER_FILE, "r") as f: user = json.load(f) # Get current stats
    user["xp"] = user.get("xp", 0) + gain           # Add XP
    new_lvl = (user["xp"] // 200) + 1               # Calculate level (1 per 200XP)
    if new_lvl > user.get("level", 1):              # Level up notification
        print(f"{Colors.GOLD}{Colors.BOLD}⭐ LEVEL UP! You are now Level {new_lvl}!{Colors.ENDC}")
    user["level"] = new_lvl                         # Update level
    with open(USER_FILE, "w") as f: json.dump(user, f, indent=4) # Save stats
    print(f"{Colors.GOLD}✨ +{gain} XP Gained!{Colors.ENDC}")

def check_deadlines():
    """Scans for deadlines and performs 'Auto-Escalation' on stagnant tasks."""
    tasks = load_tasks(); now = datetime.now(); alerts = [] # Setup
    for t in tasks:
        if not t["status"]:                         # Only check pending tasks
            created = datetime.strptime(t["created_at"], "%Y-%m-%d %H:%M:%S")
            # Auto-Escalation: High Priority tasks older than 3 days start flashing
            if (now - created).days >= 3 and t["priority"] == "High":
                t["escalated"] = True               # Trigger visual flag
                alerts.append(f"🔥 STAGNANT: {t['description']}")
            if t["due_date"] != "None":             # Check date deadlines
                due = datetime.strptime(t["due_date"], "%Y-%m-%d")
                if due < now: alerts.append(f"⚠️ OVERDUE: {t['description']}")
                elif (due - now).days <= 1: alerts.append(f"🔔 DUE SOON: {t['description']}")
    if alerts: print(f"{Colors.RED}{Colors.BOLD}" + "\n".join(alerts) + f"{Colors.ENDC}")
    save_tasks(tasks)                               # Save any escalation flags

def display_task_table(tasks_list):
    """Renders a comprehensive, color-coded UI table for all data."""
    if not tasks_list: print(f"\n{Colors.YELLOW}--- No Tasks Found ---{Colors.ENDC}"); return
    print("\n" + Colors.BOLD + Colors.HEADER + "="*145 + Colors.ENDC)
    print(f"{Colors.BOLD}{'ID':<4} | {'Category':<12} | {'Description':<25} | {'Priority':<12} | {'Due':<12} | {'Blocked By':<10} | {'Status':<10}{Colors.ENDC}")
    print("-" * 145)
    for t in tasks_list:
        p_val = t.get("priority", "Medium")         # Priority text
        # If Escalated, add flashing red; otherwise normal colors
        p_col = (Colors.RED + Colors.FLASH) if t.get("escalated") else Colors.RED if p_val == "High" else Colors.YELLOW if p_val == "Medium" else Colors.CYAN
        s_txt = f"{Colors.GREEN}Done{Colors.ENDC}" if t["status"] else f"{Colors.RED}Pending{Colors.ENDC}"
        dep = f"#{t['blocked_by']}" if t.get("blocked_by") else "None" # Show blocker ID
        print(f"{t['id']:<4} | {t.get('category',''):<12} | {t['description']:<25} | {p_col}{p_val:<12}{Colors.ENDC} | {t['due_date']:<12} | {dep:<10} | {s_txt:<10}")
    print(Colors.BOLD + Colors.HEADER + "="*145 + Colors.ENDC + "\n")

# --- UTILITIES & ROUTING ---
def toggle_timer(task_id):
    """Starts/Stops the timer; persists time even after closing app."""
    tasks = load_tasks()                            # Load
    for t in tasks:
        if t["id"] == task_id:                      # Find
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not t.get("timer_running"):          # Start path
                t["timer_running"] = True; t["start_time"] = now_str
                print(f"{Colors.GREEN}▶ Timer Started.{Colors.ENDC}")
            else:                                   # Stop path
                start = datetime.strptime(t.get("start_time", now_str), "%Y-%m-%d %H:%M:%S")
                elapsed = (datetime.now() - start).total_seconds() / 60
                t["total_minutes"] = t.get("total_minutes", 0) + elapsed
                t["timer_running"] = False          # Reset state
                print(f"{Colors.YELLOW}■ Stopped. +{elapsed:.1f}m{Colors.ENDC}")
            save_tasks(tasks); return               # Save
    print(f"{Colors.RED}✖ ID not found.{Colors.ENDC}")

def bulk_action(action_type):
    """Processes multiple task IDs for deletion or completion."""
    raw = input(f"Enter IDs to {action_type} (e.g. 1, 3, 5): ").strip()
    if not raw: return
    try:
        ids = [int(i.strip()) for i in raw.split(",")] # Parse list
        for t_id in ids:
            if action_type == "done": mark_done(t_id)
            else: delete_task(t_id)
    except: print(f"{Colors.RED}✖ Invalid ID format.{Colors.ENDC}")

def show_stats():
    """Displays productivity metrics and gamification levels."""
    tasks = load_tasks(); total = len(tasks)
    done = len([t for t in tasks if t["status"]])
    with open(USER_FILE, "r") as f: u = json.load(f) # Get player stats
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- PLAYER STATS ---{Colors.ENDC}")
    print(f"Level: {u['level']} | Total XP: {u['xp']} | Completion: {done}/{total}")
    bar = "█" * (int((done/total)*20) if total > 0 else 0) # ASCII Progress bar
    print(f"Progress: [{Colors.GREEN}{bar:<20}{Colors.ENDC}]")

# [The following helper functions are refactored for input validation]
def get_non_empty_input(p): 
    while True:
        v = input(p).strip()
        if v: return v
        print("✖ Field required.")

def get_valid_date(p):
    while True:
        v = input(p).strip()
        if not v: return "None"
        try: datetime.strptime(v, "%Y-%m-%d"); return v
        except: print("✖ Format: YYYY-MM-DD")

def get_valid_priority():
    opts = {"1":"High", "2":"Medium", "3":"Low"}
    print(f"{Colors.CYAN}(1)High (2)Med (3)Low{Colors.ENDC}")
    return opts.get(input("Select [2]: "), "Medium")

def get_category():
    tasks = load_tasks()
    cats = list(set([t.get("category", "General") for t in tasks])) # Unique categories
    print(f"{Colors.CYAN}Existing: {', '.join(cats)}{Colors.ENDC}")
    v = input("Category [General]: ").strip()
    return v if v else "General"

def delete_task(task_id):
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) < len(tasks): save_tasks(new_tasks); print(f"🗑 Deleted #{task_id}")

def view_tasks_sorted(sort_by):
    tasks = load_tasks(); p_map = {"High":1, "Medium":2, "Low":3}
    if sort_by == "priority": tasks.sort(key=lambda x: p_map.get(x["priority"], 2))
    elif sort_by == "due_date": tasks.sort(key=lambda x: (x["due_date"] == "None", x["due_date"]))
    elif sort_by == "category": tasks.sort(key=lambda x: x.get("category", "General"))
    display_task_table(tasks)

def export_to_csv():
    tasks = load_tasks()
    if not tasks: return
    with open("task_export.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=tasks[0].keys())
        writer.writeheader(); writer.writerows(tasks)
    print("✅ Exported to task_export.csv")

def archive_tasks():
    tasks = load_tasks(); done = [t for t in tasks if t["status"]]; active = [t for t in tasks if not t["status"]]
    if not done: return
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r") as f: old = json.load(f)
    else: old = []
    old.extend(done); save_tasks(active)
    with open(ARCHIVE_FILE, "w") as f: json.dump(old, f, indent=4)

# --- ROUTER & MAIN LOOP ---
def handle_choice(choice):
    """Modular routing of all menu actions."""
    if choice == "1": display_task_table(load_tasks())
    elif choice == "2": add_task(get_non_empty_input("Desc: "), get_valid_priority(), get_valid_date("Due: "), get_category())
    elif choice == "3": 
        q = input("Search Keyword/Tag/Category: ").lower()
        display_task_table([t for t in load_tasks() if q in t['description'].lower() or q in t.get('category','').lower()])
    elif choice == "4": bulk_action("done")
    elif choice == "5": bulk_action("delete")
    elif choice == "6":
        s_map = {"1": "priority", "2": "due_date", "3": "category"}
        view_tasks_sorted(s_map.get(input("Sort (1.Pri 2.Due 3.Cat): "), "id"))
    elif choice == "7":
        try: toggle_timer(int(input("Task ID: ")))
        except: print("✖ Enter numeric ID")
    elif choice == "8": show_stats()
    elif choice == "9": export_to_csv()
    elif choice == "10": archive_tasks(); print("System Offline."); return False
    return True

def main():
    """Main Application Loop."""
    check_deadlines()                               # Initial login alerts
    running = True
    while running:
        print(f"\n{Colors.BOLD}{Colors.BLUE}--- TASK MANAGER LEGENDARY ---{Colors.ENDC}")
        print("1. View All         2. Add Task         3. Search/Filter")
        print("4. Bulk Done        5. Bulk Delete      6. Sort Tasks")
        print("7. Toggle Timer     8. Player Stats     9. Export CSV")
        print("10. Archive & Exit")
        running = handle_choice(input("\nSelect (1-10): ").strip())

if __name__ == "__main__":
    if login(): main()                              # Authenticate then run