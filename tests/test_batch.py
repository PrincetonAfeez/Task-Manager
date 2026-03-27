"""Batch JSON ops with isolated data dir."""

import json

import pytest


@pytest.fixture
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setenv("TASK_MANAGER_DATA_DIR", str(tmp_path))
    yield tmp_path


def test_batch_list_empty(isolated_data):
    from tm.batch import run_batch_json

    r = run_batch_json(json.dumps({"ops": [{"op": "list_tasks"}]}))
    assert r["ok"] is True
    assert r["results"][0]["ok"] is True
    assert r["results"][0]["result"]["tasks"] == []


def test_batch_add_and_list(isolated_data):
    from tm.batch import run_batch_json

    payload = {
        "ops": [
            {
                "op": "add_task",
                "description": "Buy milk",
                "priority": "Low",
                "due_date": "None",
                "category": "Home",
                "tags": ["errand"],
            },
            {"op": "list_tasks"},
        ]
    }
    r = run_batch_json(json.dumps(payload))
    assert r["ok"] is True
    tasks = r["results"][1]["result"]["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["description"] == "Buy milk"


def test_batch_bare_array(isolated_data):
    from tm.batch import run_batch_json

    r = run_batch_json(json.dumps([{"op": "stats"}]))
    assert r["ok"] is True
    assert r["results"][0]["result"]["total"] == 0


def test_batch_unknown_op(isolated_data):
    from tm.batch import run_batch_json

    r = run_batch_json(json.dumps({"ops": [{"op": "nope"}]}))
    assert r["ok"] is False
    assert "Unknown op" in r["results"][0]["error"]
