import os
import sys

from flask import Flask, request, jsonify
import hashlib
import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.npc_api_service import (
    generate_npc,
    get_options,
    list_npcs,
    save_npc,
)
from services.forge_api_service import (
    generate_module_entity,
    get_module_options,
    get_shell_options,
    get_workbench,
    list_module_entities,
    run_workbench_action,
    save_module_entity,
)

app = Flask(__name__)

# Usuarios válidos
USERS = {
    "Kabir": "key123"
}

SECRET = "SERVER_SECRET"

LOG_FILE = "server_logs.txt"


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/<path:_path>", methods=["OPTIONS"])
def api_options(_path):
    return "", 204


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/forge/options", methods=["GET"])
def forge_options():
    return jsonify(get_options())


@app.route("/api/forge/shell", methods=["GET"])
def forge_shell():
    return jsonify(get_shell_options())


@app.route("/api/forge/modules/<module_key>/options", methods=["GET"])
def forge_module_options(module_key):
    return jsonify(get_module_options(module_key))


@app.route("/api/forge/modules/<module_key>/generate", methods=["POST"])
def forge_module_generate(module_key):
    return jsonify(generate_module_entity(module_key, request.json or {}))


@app.route("/api/forge/workbench/<module_key>", methods=["GET"])
def forge_workbench(module_key):
    return jsonify(get_workbench(module_key, request.args.to_dict()))


@app.route("/api/forge/workbench/<module_key>/<action>", methods=["POST"])
def forge_workbench_action(module_key, action):
    return jsonify(run_workbench_action(module_key, action, request.json or {}))


@app.route("/api/entities", methods=["GET"])
def entities_index():
    entity_type = request.args.get("type")
    return jsonify(list_module_entities(entity_type))


@app.route("/api/entities", methods=["POST"])
def entities_save():
    payload = request.json or {}
    entity = payload.get("entity") or {}
    world_id = payload.get("world_id")

    return jsonify(save_module_entity(entity, world_id=world_id))


@app.route("/api/npcs", methods=["GET"])
def npcs_index():
    return jsonify(list_npcs())


@app.route("/api/npcs/generate", methods=["POST"])
def npcs_generate():
    return jsonify(generate_npc(request.json or {}))


@app.route("/api/npcs", methods=["POST"])
def npcs_save():
    payload = request.json or {}
    entity = payload.get("entity") or {}
    world_id = payload.get("world_id")

    return jsonify(save_npc(entity, world_id=world_id))


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
    app.run(port=5000, debug=False, threaded=True, use_reloader=False)
