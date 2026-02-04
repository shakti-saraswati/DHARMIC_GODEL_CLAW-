#!/usr/bin/env python3
"""
Local HTTP bridge for OpenClaw ↔ Codex CLI.
"""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from bridge_queue import enqueue_task, list_pending, claim_task, respond_task, init_dirs

HOST = os.getenv("DGC_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.getenv("DGC_BRIDGE_PORT", "5056"))
TOKEN = os.getenv("DGC_BRIDGE_TOKEN", "")


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def _auth_ok(handler: BaseHTTPRequestHandler) -> bool:
    if not TOKEN:
        return True
    header = handler.headers.get("X-Bridge-Token", "")
    if header == TOKEN:
        return True
    query = parse_qs(urlparse(handler.path).query)
    return query.get("token", [""])[0] == TOKEN


class BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # quiet default logging
        return

    def do_GET(self) -> None:
        if not _auth_ok(self):
            _json_response(self, HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
            return

        path = urlparse(self.path).path
        if path == "/health":
            _json_response(self, HTTPStatus.OK, {"ok": True})
            return
        if path == "/pending":
            _json_response(self, HTTPStatus.OK, {"ok": True, "tasks": list_pending()})
            return
        _json_response(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        if not _auth_ok(self):
            _json_response(self, HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
            return

        path = urlparse(self.path).path
        body = _read_json(self)

        if path == "/enqueue":
            record = enqueue_task(
                task=body.get("task", ""),
                sender=body.get("from", "openclaw"),
                scope=body.get("scope") or [],
                output=body.get("output") or [],
                constraints=body.get("constraints") or [],
                payload=body.get("payload") or {},
            )
            _json_response(self, HTTPStatus.OK, {"ok": True, "task": record})
            return

        if path == "/claim":
            record = claim_task(task_id=body.get("id"), claimed_by=body.get("by"))
            if not record:
                _json_response(self, HTTPStatus.OK, {"ok": False, "error": "no_task"})
                return
            _json_response(self, HTTPStatus.OK, {"ok": True, "task": record})
            return

        if path == "/respond":
            record = respond_task(
                task_id=body.get("id", ""),
                status=body.get("status", "done"),
                summary=body.get("summary", ""),
                report_path=body.get("report_path"),
                patch_path=body.get("patch_path"),
                error=body.get("error"),
            )
            _json_response(self, HTTPStatus.OK, {"ok": True, "response": record})
            return

        _json_response(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})


def main() -> None:
    init_dirs()
    server = ThreadingHTTPServer((HOST, PORT), BridgeHandler)
    print(f"Bridge server listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
