from flask import Flask, request, jsonify
import hashlib
import datetime

app = Flask(__name__)

# Usuarios válidos
USERS = {
    "Kabir": "key123"
}

SECRET = "SERVER_SECRET"

LOG_FILE = "server_logs.txt"


def generate_hash(data):
    return hashlib.sha256((data + SECRET).encode()).hexdigest()


@app.route("/roll", methods=["POST"])
def roll():
    data = request.json

    user = data.get("user")
    key = data.get("api_key")

    if USERS.get(user) != key:
        return jsonify({"error": "Unauthorized"}), 403

    roll_data = data.get("roll")

    timestamp = datetime.datetime.now().isoformat()

    raw = f"{timestamp}|{user}|{roll_data}"
    hash_value = generate_hash(raw)

    line = f"{raw}|{hash_value}\n"

    with open(LOG_FILE, "a") as f:
        f.write(line)

    return jsonify({
        "status": "ok",
        "hash": hash_value
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=True)