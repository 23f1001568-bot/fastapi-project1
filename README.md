# Solve Challenge MCP Server

Implements a minimal MCP Streamable HTTP-style JSON-RPC endpoint at `/mcp`.

## Deploy on Render

1. Push these files to a GitHub repository.
2. In Render, create **New → Web Service** and connect that repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. After deploy, submit `https://YOUR-SERVICE.onrender.com/mcp` as the MCP endpoint.

The server exposes exactly one tool, `solve_challenge`. On each `tools/call`, it reads
`X-Exam-Challenge` from the HTTP headers and returns the first 16 lowercase hex characters
of SHA-256(`challenge:23f1001568@ds.study.iitm.ac.in`).

## Local test

```powershell
python -m pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

Then send an MCP `initialize` JSON-RPC request to `http://127.0.0.1:8000/mcp`.
