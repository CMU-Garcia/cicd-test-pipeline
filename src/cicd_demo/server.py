"""FastAPI application for the CI/CD demo."""

import argparse
import json
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import files

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from cicd_demo.shipping import shipping_quote


def get_app_version() -> str:
    try:
        return version("cicd-demo")
    except PackageNotFoundError:
        return "0.1.0"


app = FastAPI(
    title="CI/CD FastAPI Demo",
    description="A FastAPI web application demonstrating CI/CD pipelines",
    version=get_app_version(),
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"error": "not found"},
    )


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    try:
        body = files("cicd_demo").joinpath("resources/index.html").read_bytes()
        return HTMLResponse(content=body.decode("utf-8"), status_code=200)
    except Exception:
        fallback = """<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>CI/CD FastAPI Demo</title></head>
  <body>
    <h1>CI/CD FastAPI Demo</h1>
    <p>This page ships inside the Python wheel.</p>
    <ul>
      <li><a href="/health">Health</a></li>
      <li><a href="/docs">Interactive API Docs</a></li>
    </ul>
  </body>
</html>"""
        return HTMLResponse(content=fallback, status_code=200)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": get_app_version()}


@app.get("/api/quote")
async def quote(request: Request) -> dict[str, int]:
    params = request.query_params.getlist("subtotal_cents")
    if len(params) != 1 or not params[0].isascii() or not params[0].isdecimal():
        raise HTTPException(
            status_code=400,
            detail="provide subtotal_cents once as a non-negative integer",
        )
    try:
        subtotal = int(params[0])
        return shipping_quote(subtotal)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CI/CD demo FastAPI API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    port = args.port
    if port == 0:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((args.host if args.host != "0.0.0.0" else "127.0.0.1", 0))
            port = s.getsockname()[1]

    print(json.dumps({"host": args.host, "port": port}), flush=True)
    uvicorn.run(app, host=args.host, port=port)


if __name__ == "__main__":
    main()
