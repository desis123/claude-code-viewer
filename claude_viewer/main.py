"""FastAPI main application for Claude Code Viewer."""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .utils.jsonl_parser import JSONLParser
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
import re

# Get the package directory
PACKAGE_DIR = Path(__file__).parent

# Try to find static and templates directories
# First try relative to package (for installed package)
STATIC_DIR = PACKAGE_DIR / "static"
TEMPLATES_DIR = PACKAGE_DIR / "templates"

# If not found, try relative to parent (for development)
if not STATIC_DIR.exists():
    STATIC_DIR = PACKAGE_DIR.parent / "static"
if not TEMPLATES_DIR.exists():
    TEMPLATES_DIR = PACKAGE_DIR.parent / "templates"

# Create FastAPI app
app = FastAPI(
    title="Claude Code Conversation Viewer",
    description="View, search and browse Claude Code conversation history",
    version="1.0.0"
)

# Setup static files and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Initialize parser with custom path from environment
def get_parser():
    """Get JSONLParser instance with configured path."""
    claude_path = os.environ.get("CLAUDE_PROJECTS_PATH")
    if not claude_path:
        # Fallback to default
        claude_path = str(Path.home() / ".claude" / "projects")
    return JSONLParser(claude_path)

# Pydantic models
class Project(BaseModel):
    name: str
    display_name: str
    path: str
    session_count: int
    sessions: List[str]

class Session(BaseModel):
    id: str
    filename: str
    path: str
    size: int
    created: str
    modified: str
    created_display: str
    modified_display: str
    message_count: int
    first_message_preview: str

class Message(BaseModel):
    line_number: int
    type: str
    role: Optional[str] = None
    content: str
    display_type: str
    has_code: bool = False
    timestamp: Optional[str] = None
    uuid: Optional[str] = None

class ConversationResponse(BaseModel):
    messages: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    total_pages: int

# Custom markdown renderer with syntax highlighting
def render_markdown_with_code(text: str) -> str:
    """Render markdown with syntax highlighting for code blocks"""
    
    # Check if content already contains diff HTML - if so, preserve it
    if '<div class="diff-container">' in text:
        # This is diff content that's already HTML - just process markdown around it
        # but preserve the diff HTML blocks
        
        # Split content by diff containers to process markdown around them
        diff_parts = text.split('<div class="diff-container">')
        processed_parts = []
        
        for i, part in enumerate(diff_parts):
            if i == 0:
                # First part - before any diff, process as markdown
                processed_parts.append(process_markdown_text(part))
            else:
                # This part starts with diff content
                if '</div>' in part:
                    # Find where diff content ends
                    diff_end = part.rfind('</div>') + 6  # Include the closing tag
                    diff_html = '<div class="diff-container">' + part[:diff_end]
                    remaining_text = part[diff_end:]
                    
                    processed_parts.append(diff_html)
                    if remaining_text.strip():
                        processed_parts.append(process_markdown_text(remaining_text))
                else:
                    # Malformed diff HTML, process as regular markdown
                    processed_parts.append(process_markdown_text('<div class="diff-container">' + part))
        
        return ''.join(processed_parts)
    else:
        # Regular content without diffs
        return process_markdown_text(text)

def process_markdown_text(text: str) -> str:
    """Process text as markdown with syntax highlighting"""
    
    # Custom renderer for code blocks
    def highlight_code_block(match):
        language = match.group(1) or 'text'
        code = match.group(2)
        
        try:
            if language.lower() in ['text', 'plain', '']:
                lexer = guess_lexer(code)
            else:
                lexer = get_lexer_by_name(language.lower())
            
            formatter = HtmlFormatter(
                style='github-dark',
                cssclass='highlight',
                linenos=False
            )
            
            highlighted = highlight(code, lexer, formatter)
            return f'<div class="code-block">{highlighted}</div>'
            
        except (ClassNotFound, Exception):
            return f'<pre><code class="language-{language}">{code}</code></pre>'
    
    # Process code blocks first
    code_block_pattern = r'```(\w*)\n(.*?)\n```'
    text = re.sub(code_block_pattern, highlight_code_block, text, flags=re.DOTALL)
    
    # Process inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Convert markdown to HTML
    html = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    
    return html

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main page showing all projects"""
    parser = get_parser()
    projects = parser.get_projects()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "projects": projects
    })

@app.get("/api/projects", response_model=List[Project])
async def get_projects():
    """API endpoint to get all projects"""
    parser = get_parser()
    return parser.get_projects()

@app.get("/project/{project_name}", response_class=HTMLResponse)
async def project_view(request: Request, project_name: str):
    """Project page showing all sessions"""
    parser = get_parser()
    sessions = parser.get_sessions(project_name)
    if not sessions:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return templates.TemplateResponse("project_view.html", {
        "request": request,
        "project_name": project_name,
        "display_name": parser._format_project_name(project_name),
        "sessions": sessions
    })

@app.get("/api/sessions/{project_name}", response_model=List[Session])
async def get_sessions(project_name: str):
    """API endpoint to get sessions for a project"""
    parser = get_parser()
    sessions = parser.get_sessions(project_name)
    if not sessions:
        raise HTTPException(status_code=404, detail="Project not found")
    return sessions

@app.get("/conversation/{project_name}/{session_id}", response_class=HTMLResponse)
async def conversation_view(
    request: Request,
    project_name: str,
    session_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=200, ge=10),
    search: Optional[str] = Query(None),
    message_type: Optional[str] = Query(None)
):
    """Conversation viewer page"""
    parser = get_parser()
    conversation = parser.get_conversation(
        project_name, session_id, page, per_page, search, message_type
    )
    
    if not conversation["messages"] and page == 1:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Render markdown content
    for message in conversation["messages"]:
        if message.get("content"):
            message["rendered_content"] = render_markdown_with_code(message["content"])
    
    return templates.TemplateResponse("conversation.html", {
        "request": request,
        "project_name": project_name,
        "session_id": session_id,
        "conversation": conversation,
        "search": search,
        "message_type": message_type,
        "display_name": parser._format_project_name(project_name)
    })

@app.get("/api/conversation/{project_name}/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    project_name: str,
    session_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=200, ge=10),
    search: Optional[str] = Query(None),
    message_type: Optional[str] = Query(None)
):
    """API endpoint to get conversation data"""
    parser = get_parser()
    conversation = parser.get_conversation(
        project_name, session_id, page, per_page, search, message_type
    )
    
    return ConversationResponse(**conversation)

@app.get("/api/search-sessions/{project_name}")
async def search_sessions(
    project_name: str,
    q: str = Query(..., min_length=1),
    max_results: int = Query(20, le=100)
):
    """Search for sessions containing specific content"""
    parser = get_parser()
    results = parser.search_sessions(project_name, q, max_results)
    
    return {
        "query": q,
        "project": project_name,
        "results": results,
        "total_results": len(results)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    parser = get_parser()
    claude_path = os.environ.get("CLAUDE_PROJECTS_PATH", "Not set")
    projects_exist = os.path.exists(claude_path)
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "claude_projects_path": claude_path,
        "projects_directory_exists": projects_exist,
        "projects_count": len(parser.get_projects()) if projects_exist else 0
    }