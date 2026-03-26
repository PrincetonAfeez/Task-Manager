# Task Manager (CLI)

A **Python 3** CLI task manager with **Rich** tables and prompts, **atomic JSON** persistence, CSV import/export, recurrence, notes, filters, and optional **password gate**.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python task_manager.py
```

Or:

```bash
python -m tm
```

### Data directory

By default, `tasks.json`, `users.json`, and `archive.json` live in the **current working directory**. Override with:

```bash
set TASK_MANAGER_DATA_DIR=C:\path\to\data
python task_manager.py
```

(On PowerShell: `$env:TASK_MANAGER_DATA_DIR="C:\path\to\data"`.)

## Tests

```bash
pytest
```

## Features

| Area | Details |
|------|---------|
| **UI** | [Rich](https://github.com/Textualize/rich) tables, panels, safe password prompt |
| **Persistence** | Atomic writes (crash-safe), JSON storage |
| **Tasks** | Description, priority, due date, category, tags, notes, recurrence (daily/weekly/monthly), dependencies, timer, XP |
| **Views** | All tasks; **today + overdue**; **next 7 days** |
| **Edit** | Full edit flow + **detail** view for one task |
| **Search** | Description, category, notes, tags (`#tag` supported) |
| **Complete** | One or many IDs; recurring tasks spawn the **next occurrence** when marked done |
| **CSV** | Export (tags as `;`-separated); **import** merges/replaces by `id` |
| **Archive** | Moves completed tasks to `archive.json` and exits |

## Security

Passwords are **SHA-256** without salt—suitable for **local learning only**. Keep `users.json` private (it is listed in `.gitignore`).

## Menu

1. View all  
2. Today & overdue  
3. Next 7 days  
4. Add task  
5. Edit task  
6. Task detail  
7. Search  
8. Complete (IDs)  
9. Delete (IDs)  
10. Sort  
11. Timer  
12. Stats  
13. Export CSV  
14. Import CSV  
15. Archive & exit  

## Layout

- `task_manager.py` — entry point  
- `tm/` — package (`config`, `storage`, `users`, `tasks`, `cli`)  
- `tests/` — pytest  

The tutorial-style step history is preserved in Git history; this README reflects the **current** app.
