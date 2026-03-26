# Task Manager (CLI)

A Python CLI that demonstrates **lists/dictionaries**, **JSON persistence**, **CRUD**, and a full menu-driven workflow. Dependencies: **Python 3** only (`requirements.txt` lists no third-party packages).

## Run

```bash
python task_manager.py
```

On first run you create a local admin account (`users.json`). Task data is stored in `tasks.json`. Completed tasks can be moved to `archive.json` via **Archive & Exit**.

## Features

| Area | What it does |
|------|----------------|
| Tasks | ID, description, priority, due date, category, **tags**, status, created time, optional dependency (`blocked_by`), time tracking fields |
| Search (option 3) | Matches description, category, or **tags** (use `#work` or `work`) |
| Sort (option 6) | By priority, due date, category, or ID (default: priority) |
| Bulk | Mark done or delete by comma-separated IDs |
| Alerts | Overdue / due-soon; auto-escalation flag for stale high-priority items |
| Export | CSV (`task_export.csv`) with **all keys** present across tasks |
| Auth | Login, optional password reset via recovery Q&A |
| Extras | XP/levels on complete, colored table output |

## Task shape (main fields)

| Field | Notes |
|--------|--------|
| `tags` | List of strings (lowercased when added); older saved tasks without `tags` still load |
| `q` / `a` | Recovery question and **hashed** answer in `users.json` |

## Security note

Passwords are **SHA-256 hashes without salt**—fine for local learning, **not** for production or shared machines. `users.json` is **gitignored**; do not commit it.

## User file migration

If an older `users.json` used `recovery_question` / `recovery_answer`, it is **migrated** on load to `q` / `a`. Missing `xp` / `level` default to `0` / `1`.

## Menu (current)

1. View All  
2. Add Task  
3. Search / filter (keyword, category, `#tag`)  
4. Bulk done  
5. Bulk delete  
6. Sort (1 priority · 2 due · 3 category · 4 ID; default priority)  
7. Toggle timer  
8. Player stats  
9. Export CSV  
10. Archive completed & exit  

---

## Tutorial history (evolution)

The project grew stepwise: persistence → CRUD → priorities → search → due dates → CSV → sorting → colors → validation → security → analytics/archiving → tags/time/bulk → categories → escalation/dependencies/gamification. The README’s step list documents that learning path; the **Menu** section above is the source of truth for the current UI.
