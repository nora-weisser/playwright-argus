def main() -> None:
    """Run the Playwright Argus MCP server over stdio."""

    from playwright_argus.server import mcp

    mcp.run()
