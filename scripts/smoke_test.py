"""Check a deployed server, or start a server from an installed wheel and check it."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen


def request(base_url: str, path: str, expected_status: int):
    try:
        response = urlopen(base_url.rstrip("/") + path, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        body = response.read()
        if response.status != expected_status:
            raise RuntimeError(f"{path}: expected HTTP {expected_status}, got {response.status}")
        return body


def check_server(base_url: str, expected_version: str | None) -> None:
    health = json.loads(request(base_url, "/health", 200))
    if health.get("status") != "ok" or not health.get("version"):
        raise RuntimeError(f"unexpected health response: {health}")
    if expected_version and health["version"] != expected_version:
        raise RuntimeError(f"expected version {expected_version}, got {health['version']}")
    if b"This page ships inside the Python wheel." not in request(base_url, "/", 200):
        raise RuntimeError("packaged homepage is missing")
    for subtotal, fee in [(4999, 500), (5000, 0)]:
        quote = json.loads(request(base_url, f"/api/quote?subtotal_cents={subtotal}", 200))
        expected = {
            "subtotal_cents": subtotal,
            "shipping_cents": fee,
            "total_cents": subtotal + fee,
        }
        if quote != expected:
            raise RuntimeError(f"unexpected shipping quote: {quote}; expected {expected}")
    request(base_url, "/api/quote?subtotal_cents=-1", 400)
    request(base_url, "/missing", 404)
    print(f"Smoke test passed: {base_url}, version {health['version']}")


def check_installed(python: Path, expected_version: str | None) -> None:
    # Use a different working directory and isolated Python: source code cannot mask a bad wheel.
    with tempfile.TemporaryDirectory(prefix="cicd-smoke-") as temporary:
        log_path = Path(temporary) / "server.log"
        with log_path.open("wb") as log:
            process = subprocess.Popen(
                [str(python.resolve()), "-I", "-m", "cicd_demo", "--port", "0"],
                cwd=temporary,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    lines = log_path.read_text(encoding="utf-8").splitlines()
                    if process.poll() is not None:
                        raise RuntimeError("server exited before the smoke test")
                    if lines:
                        try:
                            address = json.loads(lines[0])
                        except json.JSONDecodeError:
                            time.sleep(0.1)
                            continue
                        check_server(f"http://127.0.0.1:{address['port']}", expected_version)
                        break
                    time.sleep(0.1)
                else:
                    raise RuntimeError("server did not start within 15 seconds")
            except Exception:
                print(log_path.read_text(encoding="utf-8"), file=sys.stderr)
                raise
            finally:
                # Windows venv python.exe can launch a child interpreter; stop both.
                if os.name == "nt" and process.poll() is None:
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True,
                        check=True,
                    )
                elif process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--python", type=Path, default=Path(sys.executable))
    mode.add_argument("--url", help="check an already running server, e.g. a Docker container")
    parser.add_argument("--expected-version")
    args = parser.parse_args()
    if args.url:
        check_server(args.url, args.expected_version)
    else:
        check_installed(args.python, args.expected_version)


if __name__ == "__main__":
    main()
