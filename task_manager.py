import json                                         # Import the library to handle JSON data files
import os                                           # Import the library to check if files exist on your PC
from datetime import datetime                       # Import the library to capture the current date and time

# --- CONFIGURATION ---
DATA_FILE = "tasks.json"                            # Define the filename where our tasks will be stored

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
def add_task(description):                          # Define function to Create a new task
    tasks = load_tasks()                            # First, get the current list of tasks from storage
    new_task = {                                    # Create a dictionary for the new task
        "id": len(tasks) + 1,                       # Set the ID by counting existing tasks and adding 1
        "description": description,                 # Store the description provided by the user
        "status": False,                            # Set default status to False (meaning 'Pending')
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Store the current timestamp as a string
    }
    tasks.append(new_task)                          # Add the new dictionary to our Python list
    save_tasks(tasks)                               # Save the updated list back to the JSON file
    print(f"✔ Task added successfully: '{description}'") # Print a success message to the user

def view_tasks():                                   # Define function to Read and display tasks
    tasks = load_tasks()                            # Get the latest list of tasks
    if not tasks:                                   # Check if the list is empty
        print("\n--- No tasks found. Your list is empty! ---") # Tell the user there's nothing to show
        return                                      # Stop the function early
    print("\n" + "="*50)                             # Print a top border for the table
    print(f"{'ID':<4} | {'Description':<20} | {'Status':<10}") # Print the table headers with alignment
    print("-" * 50)                                 # Print a separator line
    for task in tasks:                              # Loop through every task in the list
        status_text = "Done" if task["status"] else "Pending" # Convert the Boolean True/False to a word
        print(f"{task['id']:<4} | {task['description']:<20} | {status_text:<10}") # Print the task row
    print("="*50 + "\n")                            # Print a bottom border

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

# --- USER INTERFACE ---
def main():                                         # Define the primary app controller
    while True:                                     # Start an infinite loop to keep the app open
        print("\n--- TASK MANAGER MENU ---")        # Print the menu header
        print("1. View Tasks")                      # Show option 1
        print("2. Add Task")                       # Show option 2
        print("3. Mark Task Done")                  # Show option 3
        print("4. Delete Task")                     # Show option 4
        print("5. Exit")                            # Show option 5
        
        choice = input("\nChoose an option (1-5): ") # Ask the user for their choice
        
        if choice == "1":                           # If they chose 1...
            view_tasks()                            # Call the view function
        elif choice == "2":                         # If they chose 2...
            desc = input("Enter task description: ") # Ask for the task text
            add_task(desc)                          # Call the add function
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
        elif choice == "5":                         # If they chose 5...
            print("Goodbye!")                       # Print a farewell message
            break                                   # Break the loop to close the program
        else:                                       # If they typed anything else...
            print("Invalid choice, try again.")     # Prompt them to try again

if __name__ == "__main__":                          # Check if this script is being run directly
    main()                                          # Start the program by calling main()