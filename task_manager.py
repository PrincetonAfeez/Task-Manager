#Task Manger for handling asynchronous tasks in the application."

import json
import os
from datetime import datetime

# The name of our "database" file
DATA_FILE = "tasks.json"

def load_tasks():
    """Reads the JSON file and returns a list of tasks."""
    if not os.path.exists(DATA_FILE):
        return [] # Return empty list if file doesn't exist yet
    with open(DATA_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return [] # Return empty list if file is corrupted/empty

def save_tasks(tasks):
    """Takes a list of tasks and saves them to the JSON file."""
    with open(DATA_FILE, "w") as file:
        json.dump(tasks, file, indent=4)

def add_task(description):
    """Creates a new task dictionary and appends it to our JSON file."""
    tasks = load_tasks()
    
    # Create the task object based on your README schema
    new_task = {
        "id": len(tasks) + 1,
        "description": description,
        "status": False,  # False = Pending, True = Completed
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"✔ Task added successfully: '{description}'")

# --- TEMPORARY TEST BLOCK ---
# We use this to test if it works. We will remove it later!
if __name__ == "__main__":
    add_task("Test my first JSON task")

def view_tasks():
    """Prints all tasks from the JSON file in a readable format."""
    tasks = load_tasks()
    
    if not tasks:
        print("\n--- No tasks found. Your list is empty! ---")
        return

    print("\n" + "="*50)
    print(f"{'ID':<4} | {'Description':<20} | {'Status':<10}")
    print("-" * 50)

    for task in tasks:
        # Convert Boolean status to a readable string
        status_text = "Done" if task["status"] else "Pending"
        
        print(f"{task['id']:<4} | {task['description']:<20} | {status_text:<10}")
    
    print("="*50 + "\n")

# --- UPDATED TEST BLOCK ---
if __name__ == "__main__":
    # add_task("Finish Git setup") # Comment this out after first run
    view_tasks()

def mark_done(task_id):
    """Finds a task by ID and sets its status to True (Done)."""
    tasks = load_tasks()
    found = False

    for task in tasks:
        if task["id"] == task_id:
            task["status"] = True
            found = True
            break
    
    if found:
        save_tasks(tasks)
        print(f"✔ Task #{task_id} marked as completed!")
    else:
        print(f"✖ Error: Task with ID {task_id} not found.")

def delete_task(task_id):
    """Removes a task from the list by its ID."""
    tasks = load_tasks()
    
    # Create a new list that includes everything EXCEPT the ID we want to delete
    # This is a "List Comprehension" - a very Pythonic way to filter data!
    updated_tasks = [task for task in tasks if task["id"] != task_id]
    
    if len(updated_tasks) < len(tasks):
        save_tasks(updated_tasks)
        print(f"🗑 Task #{task_id} deleted successfully.")
    else:
        print(f"✖ Error: Task with ID {task_id} not found.")

def main():
    while True:
        print("\n--- TASK MANAGER MENU ---")
        print("1. View Tasks")
        print("2. Add Task")
        print("3. Mark Task Done")
        print("4. Delete Task")
        print("5. Exit")
        
        choice = input("\nChoose an option (1-5): ")
        
        if choice == "1":
            view_tasks()
        elif choice == "2":
            desc = input("Enter task description: ")
            add_task(desc)
        elif choice == "3":
            try:
                task_id = int(input("Enter Task ID to mark done: "))
                mark_done(task_id)
            except ValueError:
                print("Please enter a valid number for the ID.")
        elif choice == "4":
            try:
                task_id = int(input("Enter Task ID to delete: "))
                delete_task(task_id)
            except ValueError:
                print("Please enter a valid number for the ID.")
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
