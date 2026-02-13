"""Allow running as: cd backend && python -m mcp_server"""
from mcp_server.server import app  # noqa: F401

if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("MCP_SERVER_PORT", "8001"))
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
