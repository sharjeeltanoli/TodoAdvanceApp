"""
DEPRECATED — MCP server has moved to backend/mcp_server/server.py

The standalone MCP server now lives at the top level to avoid import
conflicts with the 'mcp' SDK package. Run it with:

    cd backend && uvicorn mcp_server.server:app --host 0.0.0.0 --port 8001

Or:

    cd backend && python -m mcp_server
"""

raise ImportError(
    "MCP server moved to backend/mcp_server/server.py. "
    "Run: uvicorn mcp_server.server:app --port 8001"
)
