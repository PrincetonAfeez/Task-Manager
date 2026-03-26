"""Task CRUD, filters, export/import, deadlines, recurrence."""

import calendar
import copy
import csv
import os
from datetime import datetime, timedelta
from typing import Any

from tm.config import paths
from tm.storage import read_json, write_json_atomic
from tm.users import load_user, save_user

RECURRENCE_CHOICES = ("none", "daily", "weekly", "monthly")
RECURRENCE_SET = set(RECURRENCE_CHOICES)


def load_tasks() -> list[dict]:
    return read_json(paths()["tasks"], [])


def save_tasks(tasks: list[dict]) -> None:
    write_json_atomic(paths()["tasks"], tasks)


def parse_tags_line(line: str) -> list[str]:
    return [x.strip().lower() for x in line.split(",") if x.strip()]


def parse_tags_import(raw: str) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    s = str(raw).strip()
    if ";" in s:
        parts = s.split(";")
    else:
        parts = s.split(",")
    return [x.strip().lower() for x in parts if x.strip()]


def add_months(dt: datetime, months: int) -> datetime:
    m = dt.month - 1 + months
    y = dt.year + m // 12
    m = m % 12 + 1
    day = min(dt.day, calendar.monthrange(y, m)[1])
    return dt.replace(year=y, month=m, day=day)


def compute_next_due(due_str: str | None, recurrence: str) -> str:
    rec = (recurrence or "none").lower()
    if rec not in RECURRENCE_CHOICES:
        rec = "none"
    if due_str and due_str != "None":
        base = datetime.strptime(due_str, "%Y-%m-%d").date()
    else:
        base = datetime.now().date()
    if rec == "none":
        return due_str or "None"
    if rec == "daily":
        nxt = base + timedelta(days=1)
    elif rec == "weekly":
        nxt = base + timedelta(days=7)
    elif rec == "monthly":
        dt = datetime.combine(base, datetime.min.time())
        nxt = add_months(dt, 1).date()
    else:
        nxt = base + timedelta(days=1)
    return nxt.strftime("%Y-%m-%d")


def _next_id(tasks: list[dict]) -> int:
    return max((t["id"] for t in tasks), default=0) + 1


def add_task(
    desc: str,
    pri: str,
    due: str,
    cat: str,
    tags: list[str],
    notes: str = "",
    recurrence: str = "none",
    blocked_by: int | None = None,
) -> None:
    tasks = load_tasks()
    new_task: dict[str, Any] = {
        "id": _next_id(tasks),
        "description": desc,
        "priority": pri,
        "due_date": due,
        "category": cat,
        "tags": tags,
        "notes": notes or "",
        "recurrence": recurrence if recurrence in RECURRENCE_SET else "none",
        "status": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_minutes": 0.0,
        "timer_running": False,
        "blocked_by": blocked_by,
    }
    tasks.append(new_task)
    save_tasks(tasks)


def award_xp(priority: str) -> tuple[int, bool, int]:
    gain = {"High": 50, "Medium": 20, "Low": 10}.get(priority, 10)
    user = load_user()
    old_lvl = user.get("level", 1)
    user["xp"] = user.get("xp", 0) + gain
    new_lvl = (user["xp"] // 200) + 1
    leveled = new_lvl > old_lvl
    user["level"] = new_lvl
    save_user(user)
    return gain, leveled, new_lvl


def mark_done(task_id: int) -> tuple[str, dict | None]:
    """Returns (message, xp_info dict or None)."""
    tasks = load_tasks()
    t = next((x for x in tasks if x["id"] == task_id), None)
    if t is None:
        return ("Task ID not found.", None)
    if t.get("blocked_by"):
        blocker = next((x for x in tasks if x["id"] == t["blocked_by"]), None)
        if blocker and not blocker["status"]:
            return (f"BLOCKED: Finish Task #{t['blocked_by']} first!", None)
    if t["status"]:
        return ("Already done.", None)
    rec = (t.get("recurrence") or "none").lower()
    if rec in RECURRENCE_SET and rec != "none":
        clone = copy.deepcopy(t)
        clone["id"] = _next_id(tasks)
        clone["status"] = False
        clone["escalated"] = False
        clone["timer_running"] = False
        clone["total_minutes"] = 0.0
        clone.pop("start_time", None)
        clone["due_date"] = compute_next_due(
            t.get("due_date") if t.get("due_date") not in (None, "None") else None,
            rec,
        )
        clone["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tasks.append(clone)
    t["status"] = True
    save_tasks(tasks)
    gain, leveled, new_lvl = award_xp(t.get("priority", "Medium"))
    return (
        f"Task #{task_id} marked done.",
        {"gain": gain, "leveled": leveled, "new_level": new_lvl},
    )


def delete_task(task_id: int) -> bool:
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) < len(tasks):
        save_tasks(new_tasks)
        return True
    return False


def get_task(task_id: int) -> dict | None:
    for t in load_tasks():
        if t["id"] == task_id:
            return t
    return None


def edit_task(task_id: int, updates: dict[str, Any]) -> bool:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] != task_id:
            continue
        for k, v in updates.items():
            if k == "blocked_by":
                if v in (None, ""):
                    t["blocked_by"] = None
                elif isinstance(v, int):
                    t["blocked_by"] = v
                elif str(v).isdigit():
                    t["blocked_by"] = int(v)
                continue
            if v is None:
                continue
            if k == "tags" and isinstance(v, str):
                t["tags"] = parse_tags_line(v)
            elif k == "due_date" and v == "":
                t["due_date"] = "None"
            else:
                t[k] = v
        if (t.get("recurrence") or "none").lower() not in RECURRENCE_SET:
            t["recurrence"] = "none"
        save_tasks(tasks)
        return True
    return False


def check_deadlines() -> list[str]:
    tasks = load_tasks()
    now = datetime.now()
    alerts: list[str] = []
    for t in tasks:
        if t["status"]:
            continue
        try:
            created = datetime.strptime(t["created_at"], "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, KeyError):
            continue
        if (now - created).days >= 3 and t.get("priority") == "High":
            t["escalated"] = True
            alerts.append(f"STAGNANT: {t.get('description', '')}")
        dd = t.get("due_date")
        if dd and dd != "None":
            try:
                due = datetime.strptime(dd, "%Y-%m-%d")
            except ValueError:
                continue
            if due < now:
                alerts.append(f"OVERDUE: {t.get('description', '')}")
            elif (due - now).days <= 1:
                alerts.append(f"DUE SOON: {t.get('description', '')}")
    save_tasks(tasks)
    return alerts


def filter_due_today(tasks: list[dict]) -> list[dict]:
    today = datetime.now().date()
    out: list[dict] = []
    for t in tasks:
        if t["status"]:
            continue
        dd = t.get("due_date")
        if not dd or dd == "None":
            continue
        try:
            d = datetime.strptime(dd, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d == today:
            out.append(t)
    return out


def filter_due_week(tasks: list[dict]) -> list[dict]:
    today = datetime.now().date()
    end = today + timedelta(days=7)
    out: list[dict] = []
    for t in tasks:
        if t["status"]:
            continue
        dd = t.get("due_date")
        if not dd or dd == "None":
            continue
        try:
            d = datetime.strptime(dd, "%Y-%m-%d").date()
        except ValueError:
            continue
        if today <= d <= end:
            out.append(t)
    return out


def filter_overdue(tasks: list[dict]) -> list[dict]:
    now = datetime.now()
    out: list[dict] = []
    for t in tasks:
        if t["status"]:
            continue
        dd = t.get("due_date")
        if not dd or dd == "None":
            continue
        try:
            due = datetime.strptime(dd, "%Y-%m-%d")
        except ValueError:
            continue
        if due < now:
            out.append(t)
    return out


def toggle_timer(task_id: int) -> str | None:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] != task_id:
            continue
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not t.get("timer_running"):
            t["timer_running"] = True
            t["start_time"] = now_str
            save_tasks(tasks)
            return "Timer started."
        start = datetime.strptime(t.get("start_time", now_str), "%Y-%m-%d %H:%M:%S")
        elapsed = (datetime.now() - start).total_seconds() / 60
        t["total_minutes"] = float(t.get("total_minutes", 0)) + elapsed
        t["timer_running"] = False
        if "start_time" in t:
            del t["start_time"]
        save_tasks(tasks)
        return f"Stopped. +{elapsed:.1f} min"
    return None


def view_tasks_sorted(sort_by: str) -> list[dict]:
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
    return tasks


def task_matches_search(t: dict, q: str) -> bool:
    if q == "":
        return True
    ql = q.lower()
    if ql in t.get("description", "").lower():
        return True
    if ql in t.get("category", "").lower():
        return True
    if ql in (t.get("notes") or "").lower():
        return True
    needle = ql[1:] if ql.startswith("#") else ql
    for tag in t.get("tags") or []:
        if needle in str(tag).lower():
            return True
    return False


def export_to_csv(export_path: str | None = None) -> str:
    tasks = load_tasks()
    if not tasks:
        return "No tasks to export."
    rows = []
    for t in tasks:
        row = dict(t)
        if isinstance(row.get("tags"), list):
            row["tags"] = ";".join(str(x) for x in row["tags"])
        rows.append(row)
    fieldnames = sorted({k for row in rows for k in row.keys()})
    path = export_path or paths()["export_csv"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path


def import_from_csv(import_path: str) -> tuple[int, str | None]:
    """Returns (imported_count, error_message)."""
    if not os.path.isfile(import_path):
        return (0, "File not found.")
    tasks = load_tasks()
    nxt = _next_id(tasks)
    count = 0
    try:
        with open(import_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return (0, "CSV has no header row.")
            for row in reader:
                desc = (row.get("description") or "").strip()
                if not desc:
                    continue
                tid = row.get("id")
                if tid and str(tid).strip().isdigit():
                    new_id = int(str(tid).strip())
                else:
                    new_id = nxt
                    nxt += 1
                pri = (row.get("priority") or "Medium").strip() or "Medium"
                due = (row.get("due_date") or row.get("due") or "").strip() or "None"
                if due != "None":
                    try:
                        datetime.strptime(due, "%Y-%m-%d")
                    except ValueError:
                        due = "None"
                cat = (row.get("category") or "General").strip() or "General"
                tags = parse_tags_import(row.get("tags") or "")
                notes = (row.get("notes") or "").strip()
                rec = (row.get("recurrence") or "none").strip().lower()
                if rec not in RECURRENCE_SET:
                    rec = "none"
                blk = row.get("blocked_by")
                blocked = int(blk) if blk and str(blk).strip().isdigit() else None
                task = {
                    "id": new_id,
                    "description": desc,
                    "priority": pri,
                    "due_date": due,
                    "category": cat,
                    "tags": tags,
                    "notes": notes,
                    "recurrence": rec,
                    "status": str(row.get("status", "")).lower() in ("true", "1", "yes"),
                    "created_at": (row.get("created_at") or "").strip()
                    or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_minutes": float(row.get("total_minutes") or 0),
                    "timer_running": False,
                    "blocked_by": blocked,
                }
                existing = [i for i, x in enumerate(tasks) if x["id"] == new_id]
                if existing:
                    tasks[existing[0]] = task
                else:
                    tasks.append(task)
                nxt = _next_id(tasks)
                count += 1
        save_tasks(tasks)
    except OSError as e:
        return (0, str(e))
    return (count, None)


def archive_tasks() -> int:
    tasks = load_tasks()
    done = [t for t in tasks if t["status"]]
    active = [t for t in tasks if not t["status"]]
    if not done:
        return 0
    ap = paths()["archive"]
    old = read_json(ap, [])
    if not isinstance(old, list):
        old = []
    old.extend(done)
    write_json_atomic(ap, old)
    save_tasks(active)
    return len(done)


def stats_snapshot() -> dict[str, Any]:
    tasks = load_tasks()
    total = len(tasks)
    done = sum(1 for t in tasks if t["status"])
    u = load_user()
    return {
        "total": total,
        "done": done,
        "level": u.get("level", 1),
        "xp": u.get("xp", 0),
    }
