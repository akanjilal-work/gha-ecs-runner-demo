#!/usr/bin/env python3
"""
Demo backend for the gha-ecs-runner live demo.

The app is deliberately trivial — the point of the demo is the *pipeline*, not
the service. It exposes two endpoints:

  GET /          -> JSON describing the running artifact: the git SHA it was
                    built from, when it was built, the image digest it is
                    running, and whether that image's signature was verified at
                    deploy time. This is what proves "the thing in front of you
                    was built on the private runner and signed in-account."
  GET /healthz   -> 200 for the ALB target-group health check.

Provenance values are injected, not invented:
  * GIT_SHA, BUILT_AT  -> baked in at build time (build args -> env).
  * IMAGE_DIGEST       -> set by the deploy job in the task definition, so the
                          app reports the exact digest the deploy admitted.
  * COSIGN_VERIFIED    -> set by the deploy job after `cosign verify` passes.

No third-party packages, so the image stays tiny and has nothing to scan but
the base. Standard library only.
"""

import json
import os
import signal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8080"))

INFO = {
    "service": "gha-ecs-runner-demo",
    "message": "Built on a private, ephemeral Fargate runner and signed in-account.",
    "git_sha": os.environ.get("GIT_SHA", "dev"),
    "built_at": os.environ.get("BUILT_AT", "unknown"),
    "image_digest": os.environ.get("IMAGE_DIGEST", "unknown"),
    "signature_verified": os.environ.get("COSIGN_VERIFIED", "false") == "true",
    "region": os.environ.get("AWS_REGION", "ca-central-1"),
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, payload):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # The live page is hosted cross-origin (GitHub Pages), so allow it to read this.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") in ("/healthz", "/health"):
            self._send(200, {"status": "ok"})
        elif self.path == "/" or self.path.startswith("/?"):
            self._send(200, INFO)
        else:
            self._send(404, {"error": "not found", "path": self.path})

    def log_message(self, fmt, *args):  # quieter, structured-ish logs
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    # Stop cleanly on SIGTERM so ECS task draining is graceful.
    signal.signal(signal.SIGTERM, lambda *_: server.shutdown())
    print(f"listening on :{PORT} digest={INFO['image_digest']} sha={INFO['git_sha']}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
