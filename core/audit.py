import hashlib
import datetime
import os

from core.config import CONFIG

LOG_PATH = "data/logs/important_rolls.log"

def ensure_log_path():
    os.makedirs("data/logs", exist_ok=True)

def generate_roll_id():
    now = datetime.datetime.now()
    return f"GWF-{now.strftime('%Y%m%d-%H%M%S-%f')}"

def generate_hash(data):
    SECRET = CONFIG["secret_key"]
    return hashlib.sha256((data + SECRET).encode()).hexdigest()

def log_roll(player, category, context, roll_type, result):
    ensure_log_path()

    timestamp = datetime.datetime.now().isoformat()
    roll_id = generate_roll_id()

    raw = f"{timestamp}|{roll_id}|{player}|{category}|{context}|{roll_type}|{result}"
    hash_value = generate_hash(raw)

    line = f"{raw}|{hash_value}\n"

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)

    return roll_id, hash_value