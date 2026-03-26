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