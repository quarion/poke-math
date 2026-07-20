"""Local authenticated proxy for smoke-testing a private Cloud Run service."""

import argparse
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urljoin

import requests

HOP_BY_HOP_HEADERS = {
    "connection",
    "content-encoding",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def identity_token() -> str:
    """Get a short-lived identity token without writing it to disk."""
    return subprocess.check_output(
        ["gcloud.cmd", "auth", "print-identity-token"],
        text=True,
    ).strip()


def handler_for(service_url: str, token: str):
    class CloudRunProxyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self._proxy()

        def do_POST(self):
            self._proxy()

        def do_PUT(self):
            self._proxy()

        def do_PATCH(self):
            self._proxy()

        def do_DELETE(self):
            self._proxy()

        def _proxy(self):
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length) if content_length else None
            headers = {
                name: value
                for name, value in self.headers.items()
                if name.lower() not in HOP_BY_HOP_HEADERS
            }
            headers["Authorization"] = f"Bearer {token}"

            upstream = requests.request(
                method=self.command,
                url=urljoin(f"{service_url}/", self.path.lstrip("/")),
                headers=headers,
                data=body,
                allow_redirects=False,
                timeout=30,
            )

            self.send_response(upstream.status_code)
            for name, value in upstream.headers.items():
                if name.lower() not in HOP_BY_HOP_HEADERS and name.lower() != "set-cookie":
                    self.send_header(name, value)
            # Production must keep Secure cookies. The localhost HTTP proxy
            # removes that attribute only on its downstream test response so
            # browser sessions can be exercised without changing the service.
            for cookie in upstream.raw.headers.getlist("Set-Cookie"):
                self.send_header("Set-Cookie", cookie.replace("; Secure", ""))
            self.send_header("Content-Length", str(len(upstream.content)))
            self.end_headers()
            self.wfile.write(upstream.content)

    return CloudRunProxyHandler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("service_url")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port),
        handler_for(args.service_url.rstrip("/"), identity_token()),
    )
    print(f"Private Cloud Run proxy listening on http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
