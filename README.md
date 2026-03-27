# Task Manager (CLI)

A **Python 3** CLI task manager with **Rich** tables and prompts, **atomic JSON** persistence, CSV import/export, recurrence, notes, filters, and optional **password gate**.

## Install

```bash
pip install -r requirements.txt
```

## Run

**Interactive UI** (login + menu):

```bash
python task_manager.py
```

Or:

```bash
python -m tm
```

With no subcommand, the Rich UI starts. Typer also accepts:

- `python -m tm --help` — root help (includes **`--install-completion`**)
- `python -m tm batch --help` — JSON batch mode

### Tab completion (Typer / Click)

This CLI is built with **[Typer](https://typer.tiangolo.com/)** (Click-based). Enable tab completion once:

```bash
python -m tm --install-completion
```

Or:

```bash
python task_manager.py --install-completion
```

Use **`--show-completion`** to print the completion script for manual install. See also `python -m tm completion`.

**Note:** [argcomplete](https://github.com/kislyuk/argcomplete) targets **argparse** CLIs. This app uses Typer, so use `--install-completion` instead of `register-python-argcomplete`.

### JSON batch mode (scripting / CI)

Run operations without the interactive menu; results are printed as JSON on stdout. Exit code **1** if any operation fails.

```bash
python -m tm batch --file ops.json
python -m tm batch -f -
echo '{"ops":[{"op":"list_tasks"}]}' | python -m tm batch --stdin
```

Compact one-line output:

```bash
python -m tm batch -s -c --stdin < ops.json
```

Set `TASK_MANAGER_DATA_DIR` so scripts use a dedicated data folder.

**Payload:** either `{"ops": [ ... ]}` or a bare JSON array `[ ... ]`. Each element is an object with an **`op`** field:

| `op` | Fields |
|------|--------|
| `list_tasks` | — |
| `add_task` | `description`, optional `priority`, `due_date`, `category`, `tags` (array or comma string), `notes`, `recurrence`, `blocked_by` |
| `mark_done` | `id` |
| `delete_task` | `id` |
| `get_task` | `id` |
| `edit_task` | `id`, `updates` (object, same keys as interactive edit) |
| `search` | `query` or `q` |
| `stats` | — |
| `export_csv` | optional `path` |
| `import_csv` | `path` |
| `archive_tasks` | — |
| `check_deadlines` | — |

Example `ops.json`:

```json
{
  "ops": [
    { "op": "add_task", "description": "Scripted task", "priority": "Medium", "category": "Auto" },
    { "op": "list_tasks" }
  ]
}
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

- `task_manager.py` — entry point (Typer)  
- `tm/` — package (`config`, `storage`, `users`, `tasks`, `cli`, `batch`, `typer_app`)  
- `tests/` — pytest  

The tutorial-style step history is preserved in Git history; this README reflects the **current** app.
