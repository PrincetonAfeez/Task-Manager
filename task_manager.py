import json                                         # Import the library to handle JSON data files
import os                                           # Import the library to check if files exist on your PC
import csv                                        # Import the library to handle CSV files (for future export feature)          
from datetime import datetime                       # Import the library to capture the current date and time

# --- CONFIGURATION ---
DATA_FILE = "tasks.json"                            # Define the filename where our tasks will be stored

# --- TERMINAL COLORS ---
class Colors:
    HEADER = '\033[95m'    # Purple
    BLUE = '\033[94m'      # Blue
    GREEN = '\033[92m'     # Green (For 'Done')
    YELLOW = '\033[93m'    # Yellow (For 'Medium')
    RED = '\033[91m'       # Red (For 'High')
    CYAN = '\033[96m'      # Cyan (For 'Low')
    ENDC = '\033[0m'       # Reset color to default
    BOLD = '\033[1m'       # Bold text

# --- STORAGE ENGINE ---
def load_tasks():                                   # Define function to pull data from the hard drive
    if not os.path.exists(DATA_FILE):               # Check if the JSON file exists in the current folder
        return []                                   # If it doesn't exist, return an empty list to start fresh
    with open(DATA_FILE, "r") as file:              # Open the file in "Read" mode
        try:                                        # Use 'try' in case the file is corrupted or empty
            return json.load(file)                  # Convert the JSON text back into a Python list of dictionaries
        except json.JSONDecodeError:                # Catch errors if the file isn't valid JSON
            return []                               # Return an empty list if an error occurs

def save_tasks(tasks):                              # Define function to push data to the hard drive
    with open(DATA_FILE, "w") as file:              # Open the file in "Write" mode (this overwrites the old data)
        json.dump(tasks, file, indent=4)            # Save the list as JSON with 4-space indentation for readability

# --- CORE LOGIC (CRUD) ---
def add_task(description, priority="Medium", due_date="None"): # Added 'due_date' here
    """Creates a new task dictionary and appends it to our JSON file."""
    tasks = load_tasks()
    
    new_task = {
        "id": len(tasks) + 1,
        "description": description,
        "priority": priority,      # Ensure this matches
        "due_date": due_date,      # Ensure this matches
        "status": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"✔ Task added successfully: '{description}'")

def export_to_csv():
    """Converts the JSON database into a CSV file for Excel/Sheets."""
    tasks = load_tasks()
    if not tasks:
        print("Nothing to export!")
        return
    
    filename = "task_export.csv"
    # Get headers from the keys of the first task dictionary
    headers = tasks[0].keys()
    
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(tasks)
    
    print(f"✅ Data exported successfully to {filename}")

def view_tasks():                                   # Define function to Read and display tasks
    tasks = load_tasks()                            # Get the latest list of tasks
    if not tasks:                                   # Check if the list is empty
        print("\n--- No tasks found. Your list is empty! ---") # Tell the user there's nothing to show
        return                                      # Stop the function early
    print("\n" + "="*85)                             # Print a top border for the table
    print(f"{'ID':<4} | {'Description':<20} | {'Priority':<10} | {'Due':<12} | {'Status':<10}")
    print("-" * 85)                                 # Print a separator line
    for task in tasks:                              # Loop through every task in the list
        status_text = "Done" if task["status"] else "Pending" # Convert the Boolean True/False to a word
        print(f"{task['id']:<4} | {task['description']:<20}| {task['priority']:<10} | {task['due_date']:<12} | {status_text:<10}")
    print("="*85 + "\n")                            # Print a bottom border

def mark_done(task_id):                             # Define function to Update a task status
    tasks = load_tasks()                            # Load existing tasks
    found = False                                   # Create a 'flag' to track if we found the ID
    for task in tasks:                              # Search through the list
        if task["id"] == task_id:                   # If the ID matches the one the user typed...
            task["status"] = True                   # Change the status to True (Done)
            found = True                            # Mark that we successfully found it
            break                                   # Exit the loop early to save time
    if found:                                       # If the task was found...
        save_tasks(tasks)                           # Save the updated list back to the file
        print(f"✔ Task #{task_id} marked as completed!") # Confirm success to the user
    else:                                           # If the loop finished and 'found' is still False...
        print(f"✖ Error: Task with ID {task_id} not found.") # Tell the user the ID was wrong

def delete_task(task_id):                           # Define function to Delete a task
    tasks = load_tasks()                            # Load the current data
    # Create a new list excluding the ID we want to delete (List Comprehension)
    updated_tasks = [t for t in tasks if t["id"] != task_id] 
    if len(updated_tasks) < len(tasks):             # If the new list is shorter, something was deleted
        save_tasks(updated_tasks)                   # Save the smaller list to the JSON file
        print(f"🗑 Task #{task_id} deleted successfully.") # Confirm deletion
    else:                                           # If the lengths are the same, nothing was deleted
        print(f"✖ Error: Task with ID {task_id} not found.") # Tell the user the ID was wrong

def search_tasks(keyword):
    """Finds tasks where the description contains the keyword."""
    tasks = load_tasks()
    # Filter the list: keep task if keyword is inside description (case-insensitive)
    results = [t for t in tasks if keyword.lower() in t["description"].lower()]
    
    if not results:
        print(f"No tasks found matching '{keyword}'")
    else:
        print(f"\n--- Search Results for '{keyword}' ---")
        for t in results:
            status = "Done" if t["status"] else "Pending"
            print(f"ID: {t['id']} | {t['description']} | [{t['priority']}] | {status}")

def view_tasks_sorted(sort_by="id"):
    """
    Loads tasks and displays them sorted by a specific criteria.
    sort_by options: 'id', 'priority', 'due_date'
    """
    tasks = load_tasks()
    if not tasks:
        print("\n--- No tasks found ---")
        return

    # Define a priority map to turn words into numbers for sorting
    # This ensures 'High' (1) comes before 'Low' (3)
    priority_order = {"High": 1, "Medium": 2, "Low": 3, "None": 4}

    if sort_by == "priority":
        tasks.sort(key=lambda x: priority_order.get(x.get("priority", "Medium"), 2))
    elif sort_by == "due_date":
        # We sort by due_date string; tasks with "None" go to the bottom
        tasks.sort(key=lambda x: (x["due_date"] == "None", x["due_date"]))
    else:
        tasks.sort(key=lambda x: x["id"])

    # Now call our existing table display logic (we can refactor view_tasks to accept a list)
    display_task_table(tasks)

def display_task_table(tasks_list):
    """Helper function to print a color-coded table."""
    print("\n" + Colors.BOLD + Colors.HEADER + "="*95 + Colors.ENDC)
    print(f"{Colors.BOLD}{'ID':<4} | {'Description':<20} | {'Priority':<10} | {'Due':<12} | {'Status':<10}{Colors.ENDC}")
    print("-" * 95)

    for t in tasks_list:
        # 1. Determine Priority Color
        p_val = t.get("priority", "Medium")
        if p_val == "High":
            p_color = Colors.RED
        elif p_val == "Medium":
            p_color = Colors.YELLOW
        else:
            p_color = Colors.CYAN
        
        # 2. Determine Status Color (Green if Done, Red if Pending)
        if t["status"]:
            s_text = f"{Colors.GREEN}Done{Colors.ENDC}"
        else:
            s_text = f"{Colors.RED}Pending{Colors.ENDC}"

        # 3. Print the row with colors
        print(f"{t['id']:<4} | {t['description']:<20} | {p_color}{p_val:<10}{Colors.ENDC} | {t['due_date']:<12} | {s_text:<10}")
    
    print(Colors.BOLD + Colors.HEADER + "="*95 + Colors.ENDC + "\n")

def get_non_empty_input(prompt):
    """Ensures the user doesn't provide a blank string."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print(f"{Colors.RED}✖ Error: This field cannot be empty.{Colors.ENDC}")

def get_valid_date(prompt):
    """Ensures the date is in YYYY-MM-DD format or allows empty for 'None'."""
    while True:
        value = input(prompt).strip()
        if not value:
            return "None"
        try:
            # Try to parse the string into a real date object
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print(f"{Colors.RED}✖ Error: Use YYYY-MM-DD (e.g., 2026-12-31).{Colors.ENDC}")

def get_valid_priority():
    """Restricts priority to specific choices."""
    options = {"1": "High", "2": "Medium", "3": "Low"}
    while True:
        print("Priority: (1) High (2) Medium (3) Low")
        choice = input("Select (1-3) [Default 2]: ").strip()
        if not choice:
            return "Medium"
        if choice in options:
            return options[choice]
        print(f"{Colors.RED}✖ Invalid choice. Please pick 1, 2, or 3.{Colors.ENDC}")

# --- USER INTERFACE ---
def main():                                         # Define the primary app controller
    while True:                                     # Start an infinite loop to keep the app open
        print("\n--- TASK MANAGER MENU ---")        # Print the menu header
        print("1. View Tasks")
        print("2. Add Task")
        print("3. Mark Task Done")
        print("4. Delete Task")
        print("5. Search Tasks")  # New Option
        print("7. Sort & View Tasks") # New Option
        print("8. Exit")
        
        choice = input("\nChoose an option (1-8): ") # Ask the user for their choice
        
        if choice == "1":                           # If they chose 1...
            view_tasks()                            # Call the view function
        elif choice == "2":
            desc = get_non_empty_input("Enter task description: ")
            pri = get_valid_priority()
            due = get_valid_date("Enter due date (YYYY-MM-DD) or [Enter] for None: ")
            add_task(desc, pri, due)                          # Call the add function
        elif choice == "3":                         # If they chose 3...
            try:                                    # Use try/except to prevent crashes on bad input
                t_id = int(input("Enter ID to mark done: ")) # Convert input string to integer
                mark_done(t_id)                      # Call the update function
            except ValueError:                      # If they typed something that isn't a number
                print("Please enter a valid number.") # Show an error
        elif choice == "4":                         # If they chose 4...
            try:
                t_id = int(input("Enter ID to delete: ")) # Convert input to integer
                delete_task(t_id)                   # Call the delete function
            except ValueError:
                print("Please enter a valid number.") # Show an error
        elif choice == "5":
            query = input("Enter search keyword: ")
            search_tasks(query)
        elif choice == "6":
            export_to_csv()
        elif choice == "7":
            print("\nSort by: (1) Priority  (2) Due Date  (3) ID")
            s_choice = input("Choice: ")
            if s_choice == "1":
                view_tasks_sorted("priority")
            elif s_choice == "2":
                view_tasks_sorted("due_date")
            else:
                view_tasks_sorted("id")
        elif choice == "8":
            print("Goodbye!")
            break                                   # Break the loop to close the program
        else:                                       # If they typed anything else...
            print("Invalid choice, try again.")     # Prompt them to try again

if __name__ == "__main__":                          # Check if this script is being run directly
    main()                                          # Start the program by calling main()