MCP Server Integration with Zoho CRM

This guide walks you through setting up an MCP (Modular Command Platform) server using Python and Node.js, integrating with Claude (via the Pro plan), and preparing your development environment in Visual Studio Code (VS Code). This setup can later be extended to communicate with Zoho CRM for conversational AI capabilities.

🚀 Prerequisites
Make sure you have the following tools installed:
- Python – A Programming language used for the server.
- Node.js – Required for backend tooling.
- Visual Studio Code (VS Code) – Code editor.
- Claude Pro Plan – Required for AI integration.
- 
📦 Installation & Project Setup
Step 1: Create a New Project Folder
1. Open Visual Studio Code.
2. Create a new folder for your MCP project.
3. Open a terminal in VS Code by navigating to: Menu > Terminal > New Terminal.
4. 
Step 2: Install uv and Initialize the Project
Install uv, a Python package manager, by running the following in PowerShell:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
Then, initialize your MCP project:
uv init mcp-server-demo
cd mcp-server-demo

Step 3: Add MCP to Project Dependencies
Add MCP to your project’s dependencies using:
uv add "mcp[cli]"

Step 4: Install MCP Server Script
Install the MCP server with your main script (e.g., main.py):
uv run mcp install main.py

⚡ Quickstart Example: Create a Simple MCP Server
Create a file named server.py and add the following code:

# Import MCP server
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")

# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()


Run the server:
python server.py

⚠️ Disclaimer
Use this code at your own risk. Officehub Tech is not responsible for any issues, data loss, or damages that may arise from its use.
