"""Paths and environment-driven data directory."""

import os


def data_dir() -> str:
    root = os.environ.get("TASK_MANAGER_DATA_DIR", ".")
    return os.path.abspath(root)


def paths() -> dict[str, str]:
    base = data_dir()
    return {
        "tasks": os.path.join(base, "tasks.json"),
        "users": os.path.join(base, "users.json"),
        "archive": os.path.join(base, "archive.json"),
        "export_csv": os.path.join(base, "task_export.csv"),
    }
