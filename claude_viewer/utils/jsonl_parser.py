import json
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re
from datetime import datetime
import difflib

class JSONLParser:
    def __init__(self, claude_projects_path: str = None):
        self.claude_projects_path = claude_projects_path or os.path.expanduser("~/.claude/projects")
    
    def get_projects(self) -> List[Dict]:
        """Scan and return all Claude Code projects"""
        projects = []
        if not os.path.exists(self.claude_projects_path):
            return projects
        
        for project_dir in os.listdir(self.claude_projects_path):
            project_path = os.path.join(self.claude_projects_path, project_dir)
            if os.path.isdir(project_path):
                # Get JSONL files in this project
                jsonl_files = [f for f in os.listdir(project_path) if f.endswith('.jsonl')]
                
                projects.append({
                    "name": project_dir,
                    "display_name": self._format_project_name(project_dir),
                    "path": project_path,
                    "session_count": len(jsonl_files),
                    "sessions": jsonl_files
                })
        
        return sorted(projects, key=lambda x: x["display_name"])
    
    def get_sessions(self, project_name: str) -> List[Dict]:
        """Get all session files for a project with metadata"""
        project_path = os.path.join(self.claude_projects_path, project_name)
        sessions = []
        
        if not os.path.exists(project_path):
            return sessions
        
        for filename in os.listdir(project_path):
            if filename.endswith('.jsonl'):
                file_path = os.path.join(project_path, filename)
                file_stats = os.stat(file_path)
                
                # Count messages in file
                message_count = self._count_messages(file_path)
                
                created_dt = datetime.fromtimestamp(file_stats.st_ctime)
                modified_dt = datetime.fromtimestamp(file_stats.st_mtime)
                
                # Get first user message preview
                first_user_message = self._get_first_user_message(file_path)
                
                sessions.append({
                    "id": filename.replace('.jsonl', ''),
                    "filename": filename,
                    "path": file_path,
                    "size": file_stats.st_size,
                    "created": created_dt.isoformat(),
                    "modified": modified_dt.isoformat(),
                    "created_display": self._format_relative_time(created_dt),
                    "modified_display": self._format_relative_time(modified_dt),
                    "message_count": message_count,
                    "first_message_preview": first_user_message
                })
        
        return sorted(sessions, key=lambda x: x["modified"], reverse=True)
    
    def get_conversation(
        self, 
        project_name: str, 
        session_id: str, 
        page: int = 1, 
        per_page: int = 50,
        search: Optional[str] = None,
        message_type: Optional[str] = None
    ) -> Dict:
        """Get paginated conversation data with optional filtering"""
        
        session_path = os.path.join(self.claude_projects_path, project_name, f"{session_id}.jsonl")
        
        if not os.path.exists(session_path):
            return {"messages": [], "total": 0, "page": page, "per_page": per_page}
        
        messages = []
        with open(session_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    
                    # Parse different message types
                    parsed_message = self._parse_message(data, line_num)
                    
                    # Apply filters
                    if self._should_include_message(parsed_message, search, message_type):
                        messages.append(parsed_message)
                        
                except json.JSONDecodeError:
                    continue
        
        # Pagination
        total = len(messages)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_messages = messages[start_idx:end_idx]
        
        return {
            "messages": paginated_messages,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def _parse_message(self, data: Dict, line_num: int) -> Dict:
        """Parse different types of JSONL messages"""
        base_message = {
            "line_number": line_num,
            "raw_type": data.get("type", "unknown"),
            "timestamp": data.get("timestamp"),
        }
        
        # Handle different message types
        if data.get("type") == "summary":
            return {
                **base_message,
                "type": "summary",
                "content": data.get("summary", ""),
                "uuid": data.get("leafUuid", ""),
                "display_type": "Summary"
            }
        elif data.get("type") in ["user", "assistant"]:
            # Direct user/assistant messages (new format)
            message_data = data.get("message", {})
            content = message_data.get("content", "")
            
            if isinstance(content, list):
                # Handle structured content (tool calls, etc.)
                content = self._parse_structured_content(content)
            
            return {
                **base_message,
                "type": "message",
                "role": data.get("type"),
                "content": content,
                "display_type": data.get("type", "").title(),
                "has_code": self._contains_code(content)
            }
        elif "role" in data:
            # Legacy format - User/Assistant messages
            content = data.get("content", "")
            if isinstance(content, list):
                # Handle structured content (tool calls, etc.)
                content = self._parse_structured_content(content)
            
            return {
                **base_message,
                "type": "message",
                "role": data.get("role"),
                "content": content,
                "display_type": data.get("role", "").title(),
                "has_code": self._contains_code(content)
            }
        else:
            # Other types (system messages, etc.)
            return {
                **base_message,
                "type": "other",
                "content": json.dumps(data, indent=2),
                "display_type": data.get("type", "Unknown").title()
            }
    
    def _parse_structured_content(self, content_list: List) -> str:
        """Parse structured content from tool calls"""
        parsed_parts = []
        for item in content_list:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    # Regular text content - preserve line breaks
                    text_content = item.get("text", "")
                    parsed_parts.append(text_content)
                elif item.get("type") == "image":
                    # Image content
                    parsed_parts.append("📷 **[Image attached]**")
                elif item.get("type") == "tool_use":
                    # Tool use - format nicely
                    tool_name = item.get("name", "unknown_tool")
                    tool_params = item.get("input", {})
                    
                    # Special handling for Edit tool calls - show as diff
                    if tool_name == "Edit" and tool_params.get("old_string") and tool_params.get("new_string"):
                        file_path = tool_params.get("file_path", "unknown_file")
                        old_string = tool_params.get("old_string", "")
                        new_string = tool_params.get("new_string", "")
                        
                        # Generate diff HTML
                        diff_html = self._generate_diff_html(old_string, new_string, file_path)
                        parsed_parts.append(f"✏️ **Edit Tool: {file_path}**\n{diff_html}")
                    else:
                        # Regular tool use - format parameters readably
                        if tool_params:
                            param_lines = []
                            for key, value in tool_params.items():
                                if isinstance(value, str) and len(value) > 100:
                                    # Truncate very long strings
                                    param_lines.append(f"  **{key}**: {value[:100]}...")
                                else:
                                    param_lines.append(f"  **{key}**: {value}")
                            params_text = "\n".join(param_lines)
                        else:
                            params_text = "  (no parameters)"
                        
                        parsed_parts.append(f"🔧 **Tool Used: {tool_name}**\n{params_text}")
                    
                elif item.get("type") == "tool_result":
                    # Tool result - handle different result types
                    result_content = item.get("content", "")
                    
                    # Check for Edit tool results with diff information
                    tool_use_result = item.get("toolUseResult", {})
                    if (tool_use_result and 
                        tool_use_result.get("oldString") and 
                        tool_use_result.get("newString")):
                        # This is an Edit tool result with diff data
                        file_path = tool_use_result.get("filePath", "unknown_file")
                        old_string = tool_use_result.get("oldString", "")
                        new_string = tool_use_result.get("newString", "")
                        
                        # Generate diff HTML for tool result
                        diff_html = self._generate_diff_html(old_string, new_string, file_path)
                        parsed_parts.append(f"✅ **Edit Result: {file_path}**\n{diff_html}")
                        
                        # Also show the regular tool output if it contains useful info
                        if isinstance(result_content, str) and result_content.strip():
                            parsed_parts.append(f"📋 **Tool Output:**\n```\n{result_content}\n```")
                    else:
                        # Regular tool result handling
                        if isinstance(result_content, str):
                            # Check if already truncated in JSONL or if we need to truncate
                            if "... (output truncated)" in result_content:
                                # Already truncated in JSONL - keep as is
                                parsed_parts.append(f"📋 **Tool Output:**\n```\n{result_content}\n```")
                            elif len(result_content) > 5000:
                                # Only truncate very long results (increased limit)
                                result_content = result_content[:5000] + "\n... (output truncated by viewer)"
                                parsed_parts.append(f"📋 **Tool Output:**\n```\n{result_content}\n```")
                            else:
                                # Show full result
                                parsed_parts.append(f"📋 **Tool Output:**\n```\n{result_content}\n```")
                        else:
                            parsed_parts.append(f"📋 **Tool Output:**\n```json\n{json.dumps(result_content, indent=2)}\n```")
                else:
                    # Unknown content type
                    parsed_parts.append(f"ℹ️ **{item.get('type', 'Unknown')}:**\n```json\n{json.dumps(item, indent=2)}\n```")
            elif isinstance(item, str):
                # Simple string content
                parsed_parts.append(item)
            else:
                # Other types
                parsed_parts.append(str(item))
        
        return "\n\n".join(parsed_parts)
    
    def _contains_code(self, content: str) -> bool:
        """Check if content contains code blocks"""
        if not isinstance(content, str):
            return False
        
        # Look for common code patterns
        code_patterns = [
            r'```[\w]*\n',  # Markdown code blocks
            r'def \w+\(',   # Python functions
            r'class \w+',   # Class definitions
            r'import \w+',  # Import statements
            r'from \w+',    # From imports
            r'<[a-zA-Z][^>]*>',  # HTML tags
            r'\$\s*\w+',    # Shell commands
        ]
        
        return any(re.search(pattern, content) for pattern in code_patterns)
    
    def _should_include_message(
        self, 
        message: Dict, 
        search: Optional[str], 
        message_type: Optional[str]
    ) -> bool:
        """Apply search and type filters"""
        
        # Type filter
        if message_type and message.get("role", "").lower() != message_type.lower():
            return False
        
        # Search filter
        if search:
            search_text = search.lower()
            content = str(message.get("content", "")).lower()
            
            if search_text not in content:
                return False
        
        return True
    
    def _count_messages(self, file_path: str) -> int:
        """Count total messages in JSONL file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0
    
    def _get_first_user_message(self, file_path: str, max_length: int = 200) -> str:
        """Get the first user message from a session for preview"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        parsed_message = self._parse_message(data, 1)
                        
                        # Check if this is a user message
                        if (parsed_message.get("role") == "user" or 
                            parsed_message.get("type") == "user" or
                            data.get("type") == "user" or
                            data.get("role") == "user"):
                            
                            content = str(parsed_message.get("content", ""))
                            if content.strip():
                                # Clean up the content - remove markdown, code blocks, etc.
                                clean_content = self._clean_preview_content(content)
                                
                                # Truncate if too long
                                if len(clean_content) > max_length:
                                    return clean_content[:max_length].strip() + "..."
                                return clean_content.strip()
                    except json.JSONDecodeError:
                        continue
            
            return "No user message found"
        except Exception as e:
            return "Error reading session"
    
    def _clean_preview_content(self, content: str) -> str:
        """Clean content for preview display"""
        import re
        
        # Remove code blocks
        content = re.sub(r'```[\s\S]*?```', '[Code]', content)
        
        # Remove inline code
        content = re.sub(r'`[^`]+`', '[Code]', content)
        
        # Remove markdown headers
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
        
        # Remove markdown bold/italic
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        
        # Remove markdown links
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        
        # Replace multiple whitespace with single space
        content = re.sub(r'\s+', ' ', content)
        
        # Remove URLs
        content = re.sub(r'https?://[^\s]+', '[URL]', content)
        
        return content
    
    def _format_project_name(self, project_dir: str) -> str:
        """Convert project directory name to readable format"""
        # Convert -media-sukhon-usbd-python-projects-converters to a readable name
        if project_dir.startswith('-'):
            # Remove leading dash and convert to path-like format
            clean_name = project_dir[1:].replace('-', '/')
            # Take last few meaningful parts
            parts = clean_name.split('/')
            if len(parts) > 3:
                return '/'.join(parts[-3:])  # Last 3 parts
            return clean_name
        
        return project_dir
    
    def _format_relative_time(self, dt: datetime) -> str:
        """Format datetime as relative time string"""
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                minutes = diff.seconds // 60
                if minutes == 0:
                    return "Just now"
                return f"{minutes} min ago"
            else:  # Less than 1 day
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = diff.days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"
    
    def _generate_diff_html(self, old_string: str, new_string: str, file_path: str = "") -> str:
        """Generate HTML diff view from old_string and new_string"""
        # Split into lines for difflib
        old_lines = old_string.splitlines(keepends=True)
        new_lines = new_string.splitlines(keepends=True)
        
        # Generate unified diff
        diff = list(difflib.unified_diff(
            old_lines, 
            new_lines, 
            fromfile=f"a/{file_path}", 
            tofile=f"b/{file_path}",
            lineterm=""
        ))
        
        if not diff:
            return f"<div class='diff-no-changes'>No changes detected in {file_path}</div>"
        
        # Parse unified diff and create HTML
        html_lines = []
        html_lines.append(f'<div class="diff-container">')
        html_lines.append(f'<div class="diff-header">📝 <strong>File:</strong> {file_path}</div>')
        html_lines.append('<div class="diff-content">')
        
        line_num_old = 0
        line_num_new = 0
        
        for line in diff:
            if line.startswith('@@'):
                # Hunk header - extract line numbers
                match = re.search(r'-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?', line)
                if match:
                    line_num_old = int(match.group(1))
                    line_num_new = int(match.group(2))
                html_lines.append(f'<div class="diff-hunk-header">{line.strip()}</div>')
            elif line.startswith('---') or line.startswith('+++'):
                # File headers - skip as we already show filename
                continue
            elif line.startswith('-'):
                # Removed line
                content = line[1:].rstrip('\n\r')
                html_lines.append(f'<div class="diff-line diff-removed">')
                html_lines.append(f'<span class="diff-line-number">{line_num_old}</span>')
                html_lines.append(f'<span class="diff-marker">-</span>')
                html_lines.append(f'<span class="diff-content">{self._escape_html(content)}</span>')
                html_lines.append('</div>')
                line_num_old += 1
            elif line.startswith('+'):
                # Added line
                content = line[1:].rstrip('\n\r')
                html_lines.append(f'<div class="diff-line diff-added">')
                html_lines.append(f'<span class="diff-line-number">{line_num_new}</span>')
                html_lines.append(f'<span class="diff-marker">+</span>')
                html_lines.append(f'<span class="diff-content">{self._escape_html(content)}</span>')
                html_lines.append('</div>')
                line_num_new += 1
            elif line.startswith(' '):
                # Context line
                content = line[1:].rstrip('\n\r')
                html_lines.append(f'<div class="diff-line diff-context">')
                html_lines.append(f'<span class="diff-line-number">{line_num_old}</span>')
                html_lines.append(f'<span class="diff-marker"> </span>')
                html_lines.append(f'<span class="diff-content">{self._escape_html(content)}</span>')
                html_lines.append('</div>')
                line_num_old += 1
                line_num_new += 1
        
        html_lines.append('</div>')  # diff-content
        html_lines.append('</div>')  # diff-container
        
        return '\n'.join(html_lines)
    
    def search_sessions(self, project_name: str, query: str, max_results: int = 20) -> List[Dict]:
        """Search for sessions containing specific content"""
        project_path = os.path.join(self.claude_projects_path, project_name)
        search_results = []
        
        if not os.path.exists(project_path):
            return search_results
        
        query_lower = query.lower()
        
        # Get all sessions in the project
        sessions = self.get_sessions(project_name)
        
        for session in sessions:
            session_id = session["id"]
            session_path = os.path.join(project_path, f"{session_id}.jsonl")
            
            try:
                matches = []
                match_count = 0
                
                with open(session_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            data = json.loads(line.strip())
                            parsed_message = self._parse_message(data, line_num)
                            content = str(parsed_message.get("content", "")).lower()
                            
                            if query_lower in content:
                                match_count += 1
                                # Extract context around the match
                                content_orig = str(parsed_message.get("content", ""))
                                preview = self._extract_search_preview(content_orig, query, 200)
                                
                                matches.append({
                                    "line": line_num,
                                    "role": parsed_message.get("role", ""),
                                    "preview": preview
                                })
                                
                                # Stop after finding enough matches for preview
                                if len(matches) >= 3:
                                    break
                                    
                        except json.JSONDecodeError:
                            continue
                
                if match_count > 0:
                    # Create preview from first few matches
                    preview_text = "<br>".join([f"<strong>{match['role'].title()}:</strong> {match['preview']}" 
                                               for match in matches[:2]])
                    
                    search_results.append({
                        "session_id": session_id,
                        "match_count": match_count,
                        "preview": preview_text,
                        "modified": session["modified"],
                        "message_count": session["message_count"]
                    })
                    
                    # Stop if we have enough results
                    if len(search_results) >= max_results:
                        break
                        
            except Exception as e:
                print(f"Error searching session {session_id}: {e}")
                continue
        
        # Sort by modification date (newest first) and match count
        search_results.sort(key=lambda x: (x["match_count"], x["modified"]), reverse=True)
        
        return search_results[:max_results]
    
    def _extract_search_preview(self, content: str, query: str, max_length: int = 200) -> str:
        """Extract preview text around search query with highlighting"""
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Find the position of the query in the content
        pos = content_lower.find(query_lower)
        if pos == -1:
            return content[:max_length] + ("..." if len(content) > max_length else "")
        
        # Calculate preview start and end positions
        start = max(0, pos - max_length // 2)
        end = min(len(content), pos + len(query) + max_length // 2)
        
        preview = content[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
        
        # Highlight the search term (case-insensitive)
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        preview = pattern.sub(lambda m: f'<span class="search-highlight">{m.group()}</span>', preview)
        
        # Escape HTML except our highlight spans
        preview = (preview.replace('&', '&amp;')
                         .replace('<', '&lt;')
                         .replace('>', '&gt;')
                         .replace('"', '&quot;'))
        
        # Restore our highlight spans
        preview = (preview.replace('&lt;span class="search-highlight"&gt;', '<span class="search-highlight">')
                         .replace('&lt;/span&gt;', '</span>'))
        
        return preview
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))