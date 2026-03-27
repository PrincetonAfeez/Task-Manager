"""JSON batch operations for scripting (no Rich / no interactive login)."""

from __future__ import annotations

import json
from typing import Any

from tm.tasks import (
    add_task,
    archive_tasks,
    check_deadlines,
    delete_task,
    edit_task,
    export_to_csv,
    get_task,
    import_from_csv,
    load_tasks,
    mark_done,
    parse_tags_line,
    stats_snapshot,
    task_matches_search,
)


def _ser(obj: Any) -> Any:
    """Make result JSON-serializable."""
    if isinstance(obj, dict):
        return {k: _ser(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_ser(x) for x in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


def dispatch_op(op: dict[str, Any]) -> dict[str, Any]:
    name = (op.get("op") or op.get("operation") or "").strip()
    if not name:
        raise ValueError("Each operation needs an 'op' field")

    if name == "list_tasks":
        return {"tasks": load_tasks()}

    if name == "add_task":
        desc = op.get("description") or op.get("desc")
        if not desc:
            raise ValueError("add_task requires description")
        raw_tags = op.get("tags")
        if isinstance(raw_tags, str):
            tags = parse_tags_line(raw_tags)
        elif isinstance(raw_tags, list):
            tags = [str(x).strip().lower() for x in raw_tags if str(x).strip()]
        else:
            tags = []
        blk = op.get("blocked_by")
        if blk is not None and str(blk).strip().isdigit():
            blocked_by = int(blk)
        else:
            blocked_by = None
        add_task(
            str(desc),
            str(op.get("priority") or "Medium"),
            str(op.get("due_date") or op.get("due") or "None"),
            str(op.get("category") or "General"),
            tags,
            notes=str(op.get("notes") or ""),
            recurrence=str(op.get("recurrence") or "none"),
            blocked_by=blocked_by,
        )
        return {"added": True}

    if name == "mark_done":
        tid = op.get("id") or op.get("task_id")
        if tid is None:
            raise ValueError("mark_done requires id")
        msg, xp = mark_done(int(tid))
        out: dict[str, Any] = {"message": msg}
        if xp:
            out["xp"] = _ser(xp)
        return out

    if name == "delete_task":
        tid = op.get("id") or op.get("task_id")
        if tid is None:
            raise ValueError("delete_task requires id")
        ok = delete_task(int(tid))
        return {"deleted": ok}

    if name == "get_task":
        tid = op.get("id") or op.get("task_id")
        if tid is None:
            raise ValueError("get_task requires id")
        t = get_task(int(tid))
        return {"task": t}

    if name == "edit_task":
        tid = op.get("id") or op.get("task_id")
        if tid is None:
            raise ValueError("edit_task requires id")
        updates = op.get("updates") or {}
        if not isinstance(updates, dict):
            raise ValueError("edit_task requires updates object")
        ok = edit_task(int(tid), updates)
        return {"updated": ok}

    if name == "search":
        q = str(op.get("query") or op.get("q") or "")
        tasks = [t for t in load_tasks() if task_matches_search(t, q.lower())]
        return {"tasks": tasks}

    if name == "stats":
        return stats_snapshot()

    if name == "export_csv":
        path = op.get("path")
        res = export_to_csv(str(path) if path else None)
        return {"path": res if res != "No tasks to export." else None, "message": res}

    if name == "import_csv":
        p = op.get("path") or op.get("file")
        if not p:
            raise ValueError("import_csv requires path")
        n, err = import_from_csv(str(p))
        if err:
            raise ValueError(err)
        return {"imported": n}

    if name == "archive_tasks":
        n = archive_tasks()
        return {"archived": n}

    if name == "check_deadlines":
        alerts = check_deadlines()
        return {"alerts": alerts}

    raise ValueError(f"Unknown op: {name}")


def run_batch_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Run a batch from a JSON object.

    Supported shapes:
      { "ops": [ {...}, ... ] }
      { "operations": [ ... ] }
    A bare array at top level is also accepted: [ {...}, ... ]
    """
    if isinstance(payload, list):
        ops = payload
    else:
        ops = payload.get("ops") or payload.get("operations")
    if not isinstance(ops, list):
        return {"ok": False, "error": "Expected 'ops' array or a top-level JSON array", "results": []}

    results: list[dict[str, Any]] = []
    for i, raw in enumerate(ops):
        if not isinstance(raw, dict):
            results.append({"ok": False, "index": i, "error": "Operation must be an object"})
            continue
        try:
            data = dispatch_op(raw)
            results.append({"ok": True, "index": i, "op": raw.get("op"), "result": _ser(data)})
        except Exception as e:
            results.append(
                {
                    "ok": False,
                    "index": i,
                    "op": raw.get("op"),
                    "error": str(e),
                }
            )

    batch_ok = all(r.get("ok") for r in results)
    return {"ok": batch_ok, "results": results}


def run_batch_json(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    return run_batch_payload(payload)
