# Task-Manager Tutorial

Task Manager will teach you about Data Structures (Lists and Dictionaries) and CRUD (Create, Read, Update, Delete) operations—the bread and butter of system architecture.

This is more advanced than a text file because it allows us to save complex data (like task status and deadlines) in a machine-readable format.

Property | Type | Description
ID | Integer | A unique identifier for the task.
Description | String | What needs to be done.
Status | Boolean | "True for completed, False for pending."
Created At | String | Timestamp for when the task was added.

Step 1: The Project Structure
Step 2: Logic for Persistence (Load & Save)
Step 3: The "C" in CRUD (Create) - ID, Description, Status, and Created At.
Step 4: The view_tasks Function (R - Read)
Step 5: The mark_done Function (U - Update)
Step 6: The delete_task Function (D - Destroy)
Step 7: Update the Menu Loop

At this point, I have persistent, CRUD-compliant Python application. I've covered:

1. File I/O (JSON)
2. Data Structures (Lists and Dictionaries)
3. Git/GitHub Workflow
4. CLI UX Design

Step 8: Adding Priority Levels
Step 9: The Search/Filter Logic
Step 10: Update the Menu (The CLI)
Step 11: Add Due Dates Feature
Step 12: Add CSV Export
Step 13: The Updated Menu Logic
Step 14: Adding a Sorting
Step 15: Updating the Menu to 8 Options
Step 16: Added the Color Engine
Step 17: Updated the Display Logic
Step 18: Adding Input Validation
Step 19: Applied Validation to the Menu

The app now has:
1. Persistent Storage (JSON)
2. Full CRUD (Create, Read, Update, Delete)
3. Advanced CLI (8 Options, Colors, Sorting)
4. Data Integrity (Validation, CSV Export)

Step 20: The Security Engine & Gateway
Step 21: Add a Forgot Password & Update the User Schema
Step 22: Adding Overdue Alerts, Analytics, and Data Archiving
Step 23: Adding Tags, Time Tracking, and Bulk Actions
Step 24: Re-mapped the menu

The Menu Mapping
1. View All: This replaces "View Tasks" (Option 1).
2. Add Task: Stays the same (Option 2).
3. Search/Tags: This merges "Search Tasks" (Option 5) with the new #Tag filtering.
4. Bulk Mark Done: This is an "Update" upgrade. It replaces the single "Mark Task Done" (Option 3) because it can do one or many tasks at once.
5. Bulk Delete: This is a "Delete" upgrade. It replaces the single "Delete Task" (Option 4).
6. Sort View: Stays the same as "Sort Tasks" (Option 6).
7. Toggle Timer: [NEW] The Time Tracker.
8. Productivity: This is "Productivity Stats" renamed for space (Option 8).
9. Archive: This is "Archive Completed" renamed for space (Option 9).
10. Export & Exit: [CONSOLIDATED] I combined "Export to CSV" (Option 7) and "Exit" (Option 10) into one final command.

Final Product:
1. Security: SHA-256 hashing and Password Recovery.
2. Data Management: JSON storage, CSV Export, and Archiving.
3. Intelligence: Proactive Deadline Alerts and Productivity Analytics.
4. Efficiency: Bulk processing and integrated Time Tracking.