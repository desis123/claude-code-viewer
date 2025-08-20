@echo off
title Claude Code Viewer
echo Starting Claude Code Viewer...
cd /d "%~dp0"
echo Server will be available at: http://127.0.0.1:6300
echo Press Ctrl+C to stop the server
uvicorn claude_viewer.main:app --host 127.0.0.1 --port 6300 --reload
pause