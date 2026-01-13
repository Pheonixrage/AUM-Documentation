#!/bin/bash
# GitHub MCP Setup Script for AUM
# Run this once to enable GitHub integration in Claude Code

echo "GitHub MCP Setup for AUM"
echo "========================"
echo ""
echo "This will enable Claude to directly interact with GitHub:"
echo "- Create and manage Pull Requests"
echo "- View and create Issues"
echo "- Browse repository code"
echo ""

# Check if token is provided as argument
if [ -z "$1" ]; then
    echo "To set up, you need a GitHub Personal Access Token."
    echo ""
    echo "How to create one:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Give it a name like 'Claude Code AUM'"
    echo "4. Select these scopes:"
    echo "   - repo (full control)"
    echo "   - read:org"
    echo "   - read:user"
    echo "5. Copy the token"
    echo ""
    echo "Then run: ./github-mcp-setup.sh YOUR_TOKEN_HERE"
    exit 1
fi

TOKEN=$1

# Add GitHub MCP to Claude Code
echo "Adding GitHub MCP server..."
claude mcp add-json github "{\"type\":\"http\",\"url\":\"https://api.githubcopilot.com/mcp\",\"headers\":{\"Authorization\":\"Bearer $TOKEN\"}}"

if [ $? -eq 0 ]; then
    echo ""
    echo "Success! GitHub MCP is now configured."
    echo "Restart Claude Code to use it."
else
    echo ""
    echo "Setup failed. Please check your token and try again."
fi
