# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""A minimal stand-in for an OSQuery Controller, used by integration tests.

It serves HTTPS on the given port with the supplied self-signed certificate and
answers the OSQuery TLS enrollment/config requests. The body of the enrollment
request is written verbatim to an output file so the test can assert that the
real daemon sent the configured enrollment secret and host identifier.

Usage::

    python3 dummy_controller.py <port> <certfile> <keyfile> <enroll_out_file>
"""

import http.server
import json
import ssl
import sys


def main() -> None:
    """Run the dummy controller until killed."""
    port = int(sys.argv[1])
    certfile = sys.argv[2]
    keyfile = sys.argv[3]
    enroll_out = sys.argv[4]

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            if self.path.endswith("/enroll"):
                with open(enroll_out, "wb") as handle:
                    handle.write(body)
                payload = {"node_key": "test-node-key", "node_invalid": False}
            else:
                # Any post-enrollment request (config, logger, ...) gets a valid,
                # empty response so the daemon considers itself enrolled.
                payload = {"node_invalid": False, "schedule": {}}
            data = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_args) -> None:
            pass

    # osquery connects via controller-uri=localhost on the same machine, so
    # binding to the loopback interface is sufficient.
    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile, keyfile)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
