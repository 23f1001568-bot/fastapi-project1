import hashlib
import json
import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

EMAIL = "23f1001568@ds.study.iitm.ac.in"
PROTOCOL_VERSION = "2025-03-26"

app = FastAPI(title="Exam MCP Server")


def rpc_result(request_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def rpc_error(request_id: Any, code: int, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


@app.get("/")
async def health():
    return {"status": "ok", "mcp_endpoint": "/mcp"}


@app.post("/mcp")
async def mcp(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
        return JSONResponse(
            rpc_error(payload.get("id") if isinstance(payload, dict) else None, -32600, "Invalid Request")
        )

    method = payload.get("method")
    request_id = payload.get("id")

    # Notifications have no id and must not receive a JSON-RPC response.
    if method == "notifications/initialized" and "id" not in payload:
        return Response(status_code=202)

    if method == "initialize":
        result = {
            "protocolVersion": payload.get("params", {}).get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "solve-challenge-mcp", "version": "1.0.0"},
        }
        return JSONResponse(rpc_result(request_id, result))

    if method == "ping":
        return JSONResponse(rpc_result(request_id, {}))

    if method == "tools/list":
        result = {
            "tools": [
                {
                    "name": "solve_challenge",
                    "description": "Returns the challenge digest for the current HTTP request.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    },
                }
            ]
        }
        return JSONResponse(rpc_result(request_id, result))

    if method == "tools/call":
        params = payload.get("params") or {}
        if params.get("name") != "solve_challenge":
            return JSONResponse(rpc_error(request_id, -32602, "Unknown tool"))

        # Read the fresh challenge from HTTP headers for every call, never from params.arguments.
        challenge = request.headers.get("x-exam-challenge", "")
        if len(challenge) != 32 or any(c not in "0123456789abcdef" for c in challenge):
            return JSONResponse(rpc_error(request_id, -32602, "Missing or invalid X-Exam-Challenge"))

        digest = hashlib.sha256(f"{challenge}:{EMAIL.strip().lower()}".encode("utf-8")).hexdigest()[:16]
        return JSONResponse(
            rpc_result(
                request_id,
                {
                    "content": [{"type": "text", "text": digest}],
                    "isError": False,
                },
            )
        )

    if method and "id" not in payload:
        return Response(status_code=202)

    return JSONResponse(rpc_error(request_id, -32601, "Method not found"))


# Some MCP clients probe this path; the actual MCP transport is POST /mcp.
@app.get("/mcp")
async def mcp_get():
    return Response(status_code=405, headers={"Allow": "POST"})
