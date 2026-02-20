from flask import Flask, request, jsonify, Response
import json
import time
import os
from pathlib import Path

app = Flask(__name__)

# Gdzie zapisywać logi (lokalnie na serwerze).
# Możesz zmienić na np. "/var/log/myapp/requests.jsonl" jeśli masz uprawnienia.
LOG_DIR = os.environ.get("LOG_DIR", "./logs")
LOG_FILE = os.environ.get("LOG_FILE", "requests.jsonl")

log_path = Path(LOG_DIR) / LOG_FILE
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


def append_jsonl(path: Path, obj: dict) -> None:
    """
    Dopisuje obiekt jako 1 linię JSON do pliku.
    """
    line = json.dumps(obj, ensure_ascii=False) + "\n"
    # Append + flush na dysk
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def catch_all(path):
    # IP: X-Forwarded-For bywa listą "client, proxy1, proxy2"
    xff = request.headers.get("X-Forwarded-For", "")
    client_ip = xff.split(",")[0].strip() if xff else request.remote_addr

    data = {
        "timestamp": int(time.time()),
        "method": request.method,
        "path": "/" + path,
        "ip": client_ip,
        "url": request.url,
        "query": request.query_string.decode(errors="replace"),
        "user_agent": request.headers.get("User-Agent"),
        "referer": request.headers.get("Referer"),
        "headers": dict(request.headers),
        # UTM-y łatwo podejrzeć wprost:
        "utm": {
            "utm_source": request.args.get("utm_source"),
            "utm_medium": request.args.get("utm_medium"),
            "utm_campaign": request.args.get("utm_campaign"),
            "utm_term": request.args.get("utm_term"),
            "utm_content": request.args.get("utm_content"),
        },
    }

    # log do stdout (Runtime Logs w DO) + do pliku
    print(json.dumps(data, ensure_ascii=False))
    try:
        append_jsonl(log_path, data)
    except Exception as e:
        # nie wysypuj requestu jeśli zapis do pliku się nie uda
        print(f"LOG_WRITE_ERROR: {e}")

    # Opcja A: prosty tekst (200)
    return Response("OK\n", status=200, mimetype="text/plain")

    # Opcja B: jeśli wolisz zwracać JSON, zamień powyższy return na:
    # return jsonify({"ok": True, "logged": True, "path": "/" + path}), 200
