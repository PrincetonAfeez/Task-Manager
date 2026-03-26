import json
import os
import csv
import hashlib
from datetime import datetime

# --- CONFIGURATION ---
DATA_FILE = "tasks.json"
USER_FILE = "users.json"
ARCHIVE_FILE = "archive.json"

# --- TERMINAL COLORS (ANSI ESCAPE CODES) ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    GOLD = '\033[33m'
    FLASH = '\033[5m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

# --- SECURITY & AUTHENTICATION ---
def hash_password(password):
    """Encodes a string into a SHA-256 hex digest for security."""
    return hashlib.sha256(password.encode()).hexdigest()

def save_user(user):
    with open(USER_FILE, "w") as f:
        json.dump(user, f, indent=4)

def migrate_user_schema(user):
    """Normalize legacy keys (recovery_question/recovery_answer) to q/a; default stats."""
    changed = False
    if "recovery_question" in user:
        if "q" not in user:
            user["q"] = user["recovery_question"]
        del user["recovery_question"]
        changed = True
    if "recovery_answer" in user:
        if "a" not in user:
            user["a"] = user["recovery_answer"]
        del user["recovery_answer"]
        changed = True
    if "xp" not in user:
        user["xp"] = 0
        changed = True
    if "level" not in user:
        user["level"] = 1
        changed = True
    return changed

def load_user():
    with open(USER_FILE, "r") as f:
        user = json.load(f)
    if migrate_user_schema(user):
        save_user(user)
    return user

def setup_account():
    """Initializes the admin account and player stats if missing."""
    if not os.path.exists(USER_FILE):
        print(f"{Colors.BOLD}{Colors.CYAN}--- INITIAL SECURITY & PLAYER SETUP ---{Colors.ENDC}")
        u = get_non_empty_input("Create Admin Username: ")
        p = get_non_empty_input("Create Admin Password: ")
        q = get_non_empty_input("Recovery Question (e.g. First Pet): ")
        a = get_non_empty_input("Answer: ")
        user_data = {
            "username": u, "password": hash_password(p),
            "q": q, "a": hash_password(a.lower()),
            "xp": 0, "level": 1
        }
        save_user(user_data)
        print(f"{Colors.GREEN}Account and Player Profile created!{Colors.ENDC}\n")

def login():
    """The gateway function that protects the app and manages recovery."""
    setup_account()
    user = load_user()
    for i in range(3, 0, -1):
        print(f"\n{Colors.BOLD}Login Required ({i} tries left). Type 'forgot' for recovery.{Colors.ENDC}")
        u_input = input("Username: ").strip()
        if u_input.lower() == 'exit': exit()
        if u_input.lower() == 'forgot':
            print(f"Question: {user['q']}")
            if hash_password(input("Answer: ").lower()) == user['a']:
                user['password'] = hash_password(get_non_empty_input("New Password: "))
                save_user(user)
                print(f"{Colors.GREEN}Password Reset!{Colors.ENDC}")
                continue
        p_input = input("Password: ").strip()
        if u_input == user["username"] and hash_password(p_input) == user["password"]:
            print(f"{Colors.GREEN}Access Granted! [Lvl {user.get('level', 1)}]{Colors.ENDC}")
            return True
    return False

# --- STORAGE ENGINE ---
def load_tasks():
    """Reads tasks from JSON; returns empty list if file is missing or broken."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_tasks(tasks):
    """Writes the task list to JSON with 4-space indentation."""
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

# --- CORE LOGIC & FEATURES ---
def parse_tags_line(line):
    return [x.strip().lower() for x in line.split(",") if x.strip()]

def add_task(desc, pri, due, cat, tags):
    """Creates a task with metadata, categories, tags, and optional dependencies."""
    tasks = load_tasks()
    print("Is this blocked by another task? (Enter ID or press Enter for none)")
    dep = input("Blocked by ID: ").strip()
    new_task = {
        "id": max([t["id"] for t in tasks], default=0) + 1,
        "description": desc, "priority": pri, "due_date": due, "category": cat,
        "tags": tags,
        "status": False, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_minutes": 0, "timer_running": False,
        "blocked_by": int(dep) if dep.isdigit() else None
    }
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"{Colors.GREEN}✔ Task added to [{cat}]!{Colors.ENDC}")

def mark_done(task_id):
    """Updates status, enforces dependencies, and awards XP."""
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            if t.get("blocked_by"):
                blocker = next((x for x in tasks if x["id"] == t["blocked_by"]), None)
                if blocker and not blocker["status"]:
                    print(f"{Colors.RED}✖ BLOCKED: Finish Task #{t['blocked_by']} first!{Colors.ENDC}")
                    return
            if not t["status"]:
                t["status"] = True
                save_tasks(tasks)
                award_xp(t["priority"])
                print(f"{Colors.GREEN}✔ Task #{task_id} marked Done!{Colors.ENDC}")
                return
    print(f"{Colors.RED}✖ Task ID not found.{Colors.ENDC}")

def award_xp(priority):
    """Calculates XP based on difficulty and handles player Level Ups."""
    gain = {"High": 50, "Medium": 20, "Low": 10}.get(priority, 10)
    user = load_user()
    user["xp"] = user.get("xp", 0) + gain
    new_lvl = (user["xp"] // 200) + 1
    if new_lvl > user.get("level", 1):
        print(f"{Colors.GOLD}{Colors.BOLD}⭐ LEVEL UP! You are now Level {new_lvl}!{Colors.ENDC}")
    user["level"] = new_lvl
    save_user(user)
    print(f"{Colors.GOLD}✨ +{gain} XP Gained!{Colors.ENDC}")

def check_deadlines():
    """Scans for deadlines and performs 'Auto-Escalation' on stagnant tasks."""
    tasks = load_tasks()
    now = datetime.now()
    alerts = []
    for t in tasks:
        if not t["status"]:
            try:
                created = datetime.strptime(t["created_at"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if (now - created).days >= 3 and t.get("priority") == "High":
                t["escalated"] = True
                alerts.append(f"🔥 STAGNANT: {t['description']}")
            if t.get("due_date") != "None" and t.get("due_date"):
                try:
                    due = datetime.strptime(t["due_date"], "%Y-%m-%d")
                except ValueError:
                    continue
                if due < now:
                    alerts.append(f"⚠️ OVERDUE: {t['description']}")
                elif (due - now).days <= 1:
                    alerts.append(f"🔔 DUE SOON: {t['description']}")
    if alerts:
        print(f"{Colors.RED}{Colors.BOLD}" + "\n".join(alerts) + f"{Colors.ENDC}")
    save_tasks(tasks)

def _format_tags_cell(t):
    tags = t.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    s = ", ".join(tags)
    return (s[:16] + "…") if len(s) > 17 else s

def display_task_table(tasks_list):
    """Renders a comprehensive, color-coded UI table for all data."""
    if not tasks_list:
        print(f"\n{Colors.YELLOW}--- No Tasks Found ---{Colors.ENDC}")
        return
    width = 160
    print("\n" + Colors.BOLD + Colors.HEADER + "=" * width + Colors.ENDC)
    print(f"{Colors.BOLD}{'ID':<4} | {'Category':<12} | {'Description':<20} | {'Tags':<18} | {'Priority':<12} | {'Due':<12} | {'Blk':<6} | {'Status':<10}{Colors.ENDC}")
    print("-" * width)
    for t in tasks_list:
        p_val = t.get("priority", "Medium")
        p_col = (Colors.RED + Colors.FLASH) if t.get("escalated") else Colors.RED if p_val == "High" else Colors.YELLOW if p_val == "Medium" else Colors.CYAN
        s_txt = f"{Colors.GREEN}Done{Colors.ENDC}" if t["status"] else f"{Colors.RED}Pending{Colors.ENDC}"
        dep = f"#{t['blocked_by']}" if t.get("blocked_by") else "—"
        tags_cell = _format_tags_cell(t)
        desc = (t.get("description", "")[:17] + "…") if len(t.get("description", "")) > 18 else t.get("description", "")
        print(f"{t['id']:<4} | {t.get('category',''):<12} | {desc:<20} | {tags_cell:<18} | {p_col}{p_val:<12}{Colors.ENDC} | {str(t.get('due_date','')):<12} | {dep:<6} | {s_txt:<10}")
    print(Colors.BOLD + Colors.HEADER + "=" * width + Colors.ENDC + "\n")

# --- UTILITIES & ROUTING ---
def toggle_timer(task_id):
    """Starts/Stops the timer; persists time even after closing app."""
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not t.get("timer_running"):
                t["timer_running"] = True
                t["start_time"] = now_str
                print(f"{Colors.GREEN}▶ Timer Started.{Colors.ENDC}")
            else:
                start = datetime.strptime(t.get("start_time", now_str), "%Y-%m-%d %H:%M:%S")
                elapsed = (datetime.now() - start).total_seconds() / 60
                t["total_minutes"] = t.get("total_minutes", 0) + elapsed
                t["timer_running"] = False
                print(f"{Colors.YELLOW}■ Stopped. +{elapsed:.1f}m{Colors.ENDC}")
            save_tasks(tasks)
            return
    print(f"{Colors.RED}✖ ID not found.{Colors.ENDC}")

def bulk_action(action_type):
    """Processes multiple task IDs for deletion or completion."""
    raw = input(f"Enter IDs to {action_type} (e.g. 1, 3, 5): ").strip()
    if not raw:
        return
    try:
        ids = [int(i.strip()) for i in raw.split(",")]
        for t_id in ids:
            if action_type == "done":
                mark_done(t_id)
            else:
                delete_task(t_id)
    except ValueError:
        print(f"{Colors.RED}✖ Invalid ID format.{Colors.ENDC}")

def show_stats():
    """Displays productivity metrics and gamification levels."""
    tasks = load_tasks()
    total = len(tasks)
    done = len([t for t in tasks if t["status"]])
    u = load_user()
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- PLAYER STATS ---{Colors.ENDC}")
    print(f"Level: {u.get('level', 1)} | Total XP: {u.get('xp', 0)} | Completion: {done}/{total}")
    bar = "█" * (int((done / total) * 20) if total > 0 else 0)
    print(f"Progress: [{Colors.GREEN}{bar:<20}{Colors.ENDC}]")

def get_non_empty_input(p):
    while True:
        v = input(p).strip()
        if v:
            return v
        print("✖ Field required.")

def get_valid_date(p):
    while True:
        v = input(p).strip()
        if not v:
            return "None"
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            print("✖ Format: YYYY-MM-DD")

def get_valid_priority():
    opts = {"1": "High", "2": "Medium", "3": "Low"}
    print(f"{Colors.CYAN}(1)High (2)Med (3)Low{Colors.ENDC}")
    return opts.get(input("Select [2]: ").strip() or "2", "Medium")

def get_category():
    tasks = load_tasks()
    cats = list(set([t.get("category", "General") for t in tasks]))
    print(f"{Colors.CYAN}Existing: {', '.join(cats)}{Colors.ENDC}")
    v = input("Category [General]: ").strip()
    return v if v else "General"

def delete_task(task_id):
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) < len(tasks):
        save_tasks(new_tasks)
        print(f"🗑 Deleted #{task_id}")

def view_tasks_sorted(sort_by):
    tasks = load_tasks()
    p_map = {"High": 1, "Medium": 2, "Low": 3}
    if sort_by == "priority":
        tasks.sort(key=lambda x: p_map.get(x.get("priority", "Medium"), 2))
    elif sort_by == "due_date":
        tasks.sort(key=lambda x: (x.get("due_date") == "None", x.get("due_date")))
    elif sort_by == "category":
        tasks.sort(key=lambda x: x.get("category", "General"))
    elif sort_by == "id":
        tasks.sort(key=lambda x: x["id"])
    display_task_table(tasks)

def task_matches_search(t, q):
    if q == "":
        return True
    ql = q.lower()
    if ql in t.get("description", "").lower():
        return True
    if ql in t.get("category", "").lower():
        return True
    needle = ql[1:] if ql.startswith("#") else ql
    for tag in t.get("tags") or []:
        if needle in str(tag).lower():
            return True
    return False

def export_to_csv():
    tasks = load_tasks()
    if not tasks:
        return
    fieldnames = sorted({k for row in tasks for k in row.keys()})
    with open("task_export.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(tasks)
    print("✅ Exported to task_export.csv")

def archive_tasks():
    tasks = load_tasks()
    done = [t for t in tasks if t["status"]]
    active = [t for t in tasks if not t["status"]]
    if not done:
        return
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, "r") as f:
                old = json.load(f)
        except json.JSONDecodeError:
            old = []
    else:
        old = []
    old.extend(done)
    save_tasks(active)
    with open(ARCHIVE_FILE, "w") as f:
        json.dump(old, f, indent=4)

# --- ROUTER & MAIN LOOP ---
def handle_choice(choice):
    """Modular routing of all menu actions."""
    if choice == "1":
        display_task_table(load_tasks())
    elif choice == "2":
        add_task(
            get_non_empty_input("Desc: "),
            get_valid_priority(),
            get_valid_date("Due: "),
            get_category(),
            parse_tags_line(input("Tags (comma-separated, optional): ").strip()),
        )
    elif choice == "3":
        q = input("Search keyword, category, or #tag: ").strip().lower()
        display_task_table([t for t in load_tasks() if task_matches_search(t, q)])
    elif choice == "4":
        bulk_action("done")
    elif choice == "5":
        bulk_action("delete")
    elif choice == "6":
        s_map = {"1": "priority", "2": "due_date", "3": "category", "4": "id"}
        choice_sort = input("Sort (1.Pri 2.Due 3.Cat 4.ID) [1]: ").strip() or "1"
        view_tasks_sorted(s_map.get(choice_sort, "priority"))
    elif choice == "7":
        try:
            toggle_timer(int(input("Task ID: ").strip()))
        except ValueError:
            print("✖ Enter numeric ID")
    elif choice == "8":
        show_stats()
    elif choice == "9":
        export_to_csv()
    elif choice == "10":
        archive_tasks()
        print("System Offline.")
        return False
    return True

def main():
    """Main Application Loop."""
    check_deadlines()
    running = True
    while running:
        print(f"\n{Colors.BOLD}{Colors.BLUE}--- TASK MANAGER LEGENDARY ---{Colors.ENDC}")
        print("1. View All         2. Add Task         3. Search/Filter")
        print("4. Bulk Done        5. Bulk Delete      6. Sort Tasks")
        print("7. Toggle Timer     8. Player Stats     9. Export CSV")
        print("10. Archive & Exit")
        running = handle_choice(input("\nSelect (1-10): ").strip())

if __name__ == "__main__":
    if login():
        main()
