import json
import os
import hashlib
import secrets

USERS_PATH = os.path.join(os.path.dirname(__file__), "users.json")


def _load():
    if not os.path.exists(USERS_PATH):
        return {}
    with open(USERS_PATH, "r") as f:
        return json.load(f)


def _save(data):
    with open(USERS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return pw_hash.hex(), salt


def add_user(username, password, is_superuser=False):
    users = _load()
    pw_hash, salt = _hash_password(password)
    users[username] = {
        "password_hash": pw_hash,
        "salt": salt,
        "is_superuser": is_superuser,
    }
    _save(users)


def verify_user(username, password):
    users = _load()
    entry = users.get(username)
    if not entry:
        return False
    pw_hash, _ = _hash_password(password, entry["salt"])
    return pw_hash == entry["password_hash"]


def is_superuser(username):
    users = _load()
    entry = users.get(username)
    return bool(entry and entry.get("is_superuser"))


def set_superuser(username, value=True):
    users = _load()
    if username in users:
        users[username]["is_superuser"] = value
        _save(users)
        return True
    return False


def list_users():
    users = _load()
    return {u: {"is_superuser": v["is_superuser"]} for u, v in users.items()}
