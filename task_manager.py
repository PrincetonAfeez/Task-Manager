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