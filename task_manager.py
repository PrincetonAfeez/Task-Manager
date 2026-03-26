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
    return hashlib.sha256(password.encode()).hexdigest() 

def setup_account():
    """Initializes the admin account if the user file is missing."""
    if not os.path.exists(USER_FILE):               
        print(f"{Colors.BOLD}{Colors.CYAN}--- INITIAL SECURITY SETUP ---{Colors.ENDC}")
        username = get_non_empty_input("Create Admin Username: ") 
        password = get_non_empty_input("Create Admin Password: ") 
        print(f"\n{Colors.YELLOW}Set a Recovery Question (to reset if forgotten){Colors.ENDC}")
        question = get_non_empty_input("Question (e.g., Favorite City): ") 
        answer = get_non_empty_input("Answer: ")                  
        
        user_data = {
            "username": username,
            "password": hash_password(password),    
            "recovery_question": question,
            "recovery_answer": hash_password(answer.lower()) 
        }
        with open(USER_FILE, "w") as f:             
            json.dump(user_data, f, indent=4)
        print(f"{Colors.GREEN}Account created successfully!{Colors.ENDC}\n")

def reset_password():
    """Validates the recovery question to allow password modification."""
    if not os.path.exists(USER_FILE): return False  
    with open(USER_FILE, "r") as f:
        data = json.load(f)                         
    print(f"\n{Colors.BOLD}--- PASSWORD RECOVERY ---{Colors.ENDC}")
    print(f"Question: {data['recovery_question']}")
    ans_input = input("Your Answer: ").strip().lower() 
    if hash_password(ans_input) == data['recovery_answer']: 
        new_p = get_non_empty_input("Enter New Password: ") 
        data['password'] = hash_password(new_p)     
        with open(USER_FILE, "w") as f:
            json.dump(data, f, indent=4)            
        print(f"{Colors.GREEN}Password updated! You may now login.{Colors.ENDC}")
        return True                                 
    print(f"{Colors.RED}Incorrect answer. Recovery failed.{Colors.ENDC}")
    return False                                    

def login():
    """The gateway function that protects the app on startup."""
    setup_account()                                 
    if not os.path.exists(USER_FILE): return False  
    with open(USER_FILE, "r") as f:
        stored = json.load(f)                       
    attempts = 3                                    
    while attempts > 0:
        print(f"\n{Colors.BOLD}Login Required ({attempts} tries left){Colors.ENDC}")
        print("Tip: Type 'forgot' for recovery or 'exit' to quit.")
        u_input = input("Username: ").strip()       
        if u_input.lower() == 'exit': exit()        
        if u_input.lower() == 'forgot':             
            if reset_password(): attempts = 3; continue 
            else: attempts -= 1; continue           
        p_input = input("Password: ").strip()       
        if u_input == stored["username"] and hash_password(p_input) == stored["password"]:
            print(f"{Colors.GREEN}Access Granted. Welcome, {u_input}!{Colors.ENDC}")
            return True                             
        attempts -= 1                               
        print(f"{Colors.RED}Invalid credentials.{Colors.ENDC}")
    return False                                    

# --- STORAGE ENGINE ---
def load_tasks():
    """Reads tasks from JSON and returns them as a Python list."""
    if not os.path.exists(DATA_FILE): return []     
    with open(DATA_FILE, "r") as file:
        try: return json.load(file)                 
        except json.JSONDecodeError: return []      

def save_tasks(tasks):
    """Writes the current task list into the JSON file with pretty-print."""
    with open(DATA_FILE, "w") as file:
        json.dump(tasks, file, indent=4)            

# --- CORE LOGIC (CRUD & DASHBOARD) ---
def add_task(description, priority="Medium", due_date="None", category="General"):
    """Appends a new task dictionary to the master database."""
    tasks = load_tasks()                            
    new_task = {
        "id": max([t["id"] for t in tasks], default=0) + 1, 
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "category": category,                       # New Category field
        "status": False,                            
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_minutes": 0,                         
        "timer_running": False                      
    }
    tasks.append(new_task)                          
    save_tasks(tasks)                               
    print(f"{Colors.GREEN}✔ Task added successfully to [{category}]!{Colors.ENDC}")

def display_task_table(tasks_list):
    """A reusable UI engine to print data in a color-coded table format."""
    if not tasks_list:                              
        print(f"\n{Colors.YELLOW}--- No tasks to display ---{Colors.ENDC}")
        return
    # Expanded width for Category column
    print("\n" + Colors.BOLD + Colors.HEADER + "="*135 + Colors.ENDC)
    print(f"{Colors.BOLD}{'ID':<4} | {'Category':<12} | {'Description':<25} | {'Priority':<10} | {'Due':<12} | {'Time (m)':<8} | {'Status':<10}{Colors.ENDC}")
    print("-" * 135)                                
    for t in tasks_list:                            
        p_val = t.get("priority", "Medium")
        p_col = Colors.RED if p_val == "High" else Colors.YELLOW if p_val == "Medium" else Colors.CYAN
        s_txt = f"{Colors.GREEN}Done{Colors.ENDC}" if t["status"] else f"{Colors.RED}Pending{Colors.ENDC}"
        cat = t.get("category", "General")
        t_min = f"{t.get('total_minutes', 0):.1f}"   
        t_active = f"{Colors.BLUE}▶{Colors.ENDC} " if t.get("timer_running") else "  "
        print(f"{t['id']:<4} | {cat:<12} | {t['description']:<25} | {p_col}{p_val:<10}{Colors.ENDC} | {t['due_date']:<12} | {t_active}{t_min:<8} | {s_txt:<10}")
    print(Colors.BOLD + Colors.HEADER + "="*135 + Colors.ENDC + "\n")

def search_tasks(query):
    """Filters tasks based on keyword, #tag, or category name."""
    tasks = load_tasks()
    query = query.lower()
    results = [t for t in tasks if query in t["description"].lower() or query in t.get("category", "General").lower()]
    display_task_table(results)                     

def view_tasks_sorted(sort_by):
    """Orders tasks based on priority weight, due date, category, or ID."""
    tasks = load_tasks()
    if not tasks: return
    p_map = {"High": 1, "Medium": 2, "Low": 3, "None": 4} 
    if sort_by == "priority": tasks.sort(key=lambda x: p_map.get(x["priority"], 2))
    elif sort_by == "due_date": tasks.sort(key=lambda x: (x["due_date"] == "None", x["due_date"]))
    elif sort_by == "category": tasks.sort(key=lambda x: x.get("category", "General"))
    else: tasks.sort(key=lambda x: x["id"])         
    display_task_table(tasks)                       

def mark_done(task_id):
    """Updates a task's status to True."""
    tasks = load_tasks()
    found = False
    for t in tasks:
        if t["id"] == task_id:                      
            t["status"] = True                      
            found = True; break                     
    if found: 
        save_tasks(tasks)
        print(f"{Colors.GREEN}✔ Task #{task_id} completed!{Colors.ENDC}")
    else: print(f"{Colors.RED}✖ Task ID #{task_id} not found.{Colors.ENDC}")

def delete_task(task_id):
    """Removes a task entry permanently."""
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) < len(tasks):                 
        save_tasks(new_tasks)
        print(f"{Colors.CYAN}🗑 Task #{task_id} deleted.{Colors.ENDC}")
    else: print(f"{Colors.RED}✖ Task ID #{task_id} not found.{Colors.ENDC}")

def export_to_csv():
    """Generates a CSV file of the current task list."""
    tasks = load_tasks()
    if not tasks: print(f"{Colors.RED}Nothing to export!{Colors.ENDC}"); return
    filename = "task_export.csv"
    with open(filename, "w", newline="") as f:      
        writer = csv.DictWriter(f, fieldnames=tasks[0].keys()) 
        writer.writeheader(); writer.writerows(tasks) 
    print(f"{Colors.CYAN}✅ Exported to {filename}{Colors.ENDC}")

def check_deadlines():
    """Scans for overdue or upcoming tasks."""
    tasks = load_tasks(); now = datetime.now()
    overdue, soon = [], []                          
    for t in tasks:
        if t["due_date"] != "None" and not t["status"]:
            try:
                due = datetime.strptime(t["due_date"], "%Y-%m-%d")
                if due < now: overdue.append(t["description"]) 
                elif (due - now).days <= 1: soon.append(t["description"]) 
            except ValueError: continue             
    if overdue: print(f"{Colors.RED}{Colors.BOLD}⚠️ OVERDUE: {', '.join(overdue)}{Colors.ENDC}")
    if soon: print(f"{Colors.YELLOW}{Colors.BOLD}🔔 DUE SOON (24h): {', '.join(soon)}{Colors.ENDC}")

def show_stats():
    """Visual dashboard for productivity metrics."""
    tasks = load_tasks()
    if not tasks: print("No tasks for stats."); return
    total = len(tasks)                              
    done = len([t for t in tasks if t["status"]])   
    total_time = sum(t.get("total_minutes", 0) for t in tasks)
    percent = (done / total) * 100 if total > 0 else 0
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- STATS DASHBOARD ---{Colors.ENDC}")
    print(f"Total: {total} | Completed: {done} | Time Spent: {total_time:.1f} mins")
    
    # Category breakdown
    cats = {}
    for t in tasks:
        c = t.get("category", "General")
        cats[c] = cats.get(c, 0) + 1
    print(f"Categories: {', '.join([f'{k}({v})' for k,v in cats.items()])}")

    print(f"Success Rate: {percent:.1f}%")
    bar = "█" * int(percent // 5) + "-" * (20 - int(percent // 5)) 
    print(f"Progress: [{Colors.GREEN}{bar}{Colors.ENDC}]")

def archive_tasks():
    """Moves 'Done' tasks to archive.json."""
    tasks = load_tasks()
    done = [t for t in tasks if t["status"]]        
    active = [t for t in tasks if not t["status"]]  
    if not done: return 
    old_archive = []
    if os.path.exists(ARCHIVE_FILE):                
        with open(ARCHIVE_FILE, "r") as f:
            try: old_archive = json.load(f)
            except: pass
    old_archive.extend(done)                        
    with open(ARCHIVE_FILE, "w") as f: json.dump(old_archive, f, indent=4)
    save_tasks(active)                              

def bulk_action(action_type):
    """Handles multiple IDs for completion or deletion."""
    raw_ids = input(f"IDs to {action_type} (e.g. 1, 2, 5): ").strip()
    if not raw_ids: return
    try:
        target_ids = [int(i.strip()) for i in raw_ids.split(",")]
        for t_id in target_ids:
            if action_type == "done": mark_done(t_id)
            elif action_type == "delete": delete_task(t_id)
    except ValueError: print(f"{Colors.RED}✖ Error: Use numbers and commas only.{Colors.ENDC}")

def toggle_timer(task_id):
    """Starts/Stops a task timer."""
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not t.get("timer_running"):
                t["timer_running"] = True
                t["start_time"] = now_str
                print(f"{Colors.GREEN}▶ Timer started for Task #{task_id}{Colors.ENDC}")
            else:
                start = datetime.strptime(t.get("start_time", now_str), "%Y-%m-%d %H:%M:%S")
                elapsed = (datetime.now() - start).total_seconds() / 60
                t["total_minutes"] = t.get("total_minutes", 0) + elapsed
                t["timer_running"] = False
                print(f"{Colors.YELLOW}■ Timer stopped. Added {elapsed:.1f} mins.{Colors.ENDC}")
            save_tasks(tasks)
            return
    print(f"{Colors.RED}✖ Task ID #{task_id} not found.{Colors.ENDC}")

# --- VALIDATION UTILITIES ---
def get_non_empty_input(prompt):
    """Prompt that rejects blank strings."""
    while True:
        v = input(prompt).strip()
        if v: return v                              
        print(f"{Colors.RED}✖ Cannot be empty.{Colors.ENDC}")

def get_valid_date(prompt):
    """Prompt for YYYY-MM-DD or empty."""
    while True:
        v = input(prompt).strip()
        if not v: return "None"                     
        try:
            datetime.strptime(v, "%Y-%m-%d")        
            return v
        except ValueError: print(f"{Colors.RED}✖ Use YYYY-MM-DD format.{Colors.ENDC}")

def get_valid_priority():
    """Prompt for 1-3 priority selection."""
    opts = {"1": "High", "2": "Medium", "3": "Low"}
    while True:
        print(f"{Colors.CYAN}Priority: (1) High (2) Medium (3) Low{Colors.ENDC}")
        c = input("Select 1-3 [Default 2]: ").strip()
        if not c: return "Medium"                   
        if c in opts: return opts[c]                
        print(f"{Colors.RED}✖ Invalid Choice.{Colors.ENDC}")

def get_category():
    """Handles category selection or custom creation."""
    tasks = load_tasks()
    # Find existing unique categories
    existing = list(set([t.get("category", "General") for t in tasks]))
    print(f"\n{Colors.CYAN}Categories: {', '.join(existing)}{Colors.ENDC}")
    c = input("Type existing category or new name [Default General]: ").strip()
    return c if c else "General"

# --- ROUTING & MENU ---
def handle_choice(choice):
    """Routes user input to the correct function."""
    if choice == "1": display_task_table(load_tasks())
    elif choice == "2":
        desc = get_non_empty_input("Description: ")
        pri = get_valid_priority()
        due = get_valid_date("Due Date: ")
        cat = get_category()
        add_task(desc, pri, due, cat)
    elif choice == "3": 
        search_tasks(input("Search Keyword, #Tag, or Category: "))
    elif choice == "4": bulk_action("done")
    elif choice == "5": bulk_action("delete")
    elif choice == "6":
        print("\nSort by: (1) Priority (2) Due Date (3) Category (4) ID")
        s_map = {"1": "priority", "2": "due_date", "3": "category", "4": "id"}
        view_tasks_sorted(s_map.get(input("Choice: "), "id"))
    elif choice == "7":
        try: toggle_timer(int(input("Task ID to Start/Stop: ")))
        except ValueError: print(f"{Colors.RED}✖ Enter a numeric ID.{Colors.ENDC}")
    elif choice == "8": show_stats()
    elif choice == "9": export_to_csv()
    elif choice == "10": 
        archive_tasks() 
        print(f"{Colors.CYAN}Session archived. Goodbye!{Colors.ENDC}")
        return False 
    else: print(f"{Colors.RED}✖ Invalid choice (1-10).{Colors.ENDC}")
    return True 

def main():
    """Displays the menu and drives the application."""
    check_deadlines()                               
    running = True
    while running:
        print(f"\n{Colors.BOLD}{Colors.BLUE}--- TASK MANAGER ULTIMATE ---{Colors.ENDC}")
        print("1. View All         2. Add Task         3. Search/Filter")
        print("4. Bulk Done        5. Bulk Delete      6. Sort Tasks")
        print("7. Toggle Timer     8. Productivity     9. Export CSV")
        print("10. Archive & Exit")
        
        running = handle_choice(input("\nSelect (1-10): ").strip())

if __name__ == "__main__":
    if login(): main()                              
    else: exit()