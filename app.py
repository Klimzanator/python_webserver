from flask import Flask, request
import json
import time

app = Flask(__name__)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    data = {
        "timestamp": int(time.time()),
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "url": request.url,
        "query": request.query_string.decode(),
        "user_agent": request.headers.get("User-Agent"),
        "referer": request.headers.get("Referer"),
        "headers": dict(request.headers),
    }

    print(json.dumps(data, ensure_ascii=False))

    return "", 204
