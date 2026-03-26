"""Authentication and user profile (XP / level)."""

import hashlib

from tm.config import paths
from tm.storage import read_json, write_json_atomic


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def save_user(user: dict) -> None:
    write_json_atomic(paths()["users"], user)


def migrate_user_schema(user: dict) -> bool:
    changed = False
    if "recovery_question" in user:
        if "q" not in user:
            user["q"] = user["recovery_question"]
        del user["recovery_question"]
        changed = True
    if "recovery_answer" in user:
        if "a" not in user:
            user["a"] = user["recovery_answer"]
        del user["recovery_answer"]
        changed = True
    if "xp" not in user:
        user["xp"] = 0
        changed = True
    if "level" not in user:
        user["level"] = 1
        changed = True
    return changed


def load_user() -> dict:
    user = read_json(paths()["users"], {})
    if migrate_user_schema(user):
        save_user(user)
    return user


def setup_account_if_missing(get_non_empty_input) -> None:
    import os

    p = paths()["users"]
    if not os.path.exists(p):
        print("\n--- INITIAL SECURITY & PLAYER SETUP ---")
        u = get_non_empty_input("Create Admin Username: ")
        pw = get_non_empty_input("Create Admin Password: ")
        q = get_non_empty_input("Recovery Question (e.g. First Pet): ")
        a = get_non_empty_input("Answer: ")
        user_data = {
            "username": u,
            "password": hash_password(pw),
            "q": q,
            "a": hash_password(a.lower()),
            "xp": 0,
            "level": 1,
        }
        save_user(user_data)
        print("Account and Player Profile created!\n")
