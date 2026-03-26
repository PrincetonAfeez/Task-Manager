"""Unit tests for task helpers (no JSON I/O)."""

from tm.tasks import (
    compute_next_due,
    parse_tags_import,
    parse_tags_line,
    task_matches_search,
)


def test_parse_tags_line():
    assert parse_tags_line("a, B, c") == ["a", "b", "c"]
    assert parse_tags_line("") == []


def test_parse_tags_import():
    assert parse_tags_import("a;b;c") == ["a", "b", "c"]
    assert parse_tags_import("a, b") == ["a", "b"]


def test_compute_next_due_daily():
    assert compute_next_due("2025-01-01", "daily") == "2025-01-02"


def test_compute_next_due_weekly():
    assert compute_next_due("2025-01-01", "weekly") == "2025-01-08"


def test_compute_next_due_monthly():
    assert compute_next_due("2025-01-15", "monthly") == "2025-02-15"


def test_task_matches_search():
    t = {
        "description": "Hello World",
        "category": "Work",
        "tags": ["urgent", "home"],
        "notes": "secret note",
    }
    assert task_matches_search(t, "hello")
    assert task_matches_search(t, "work")
    assert task_matches_search(t, "urgent")
    assert task_matches_search(t, "#home")
    assert task_matches_search(t, "secret")
    assert not task_matches_search(t, "zzz")
