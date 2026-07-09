import hashlib

SECRET = "GWF_SECRET_KEY"

def generate_hash(data):
    return hashlib.sha256((data + SECRET).encode()).hexdigest()

def verify_line(log_line):
    parts = log_line.strip().split("|")

    # Último elemento es el hash
    stored_hash = parts[-1]
    raw_data = "|".join(parts[:-1])

    recalculated = generate_hash(raw_data)

    return stored_hash == recalculated