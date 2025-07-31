# Claude Code Viewer 🔍

Beautiful web interface for browsing your Claude Code conversation history with search, filtering, and syntax highlighting.

![Claude Code Viewer](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)

## ✨ Features

- 🔍 **Search conversations** - Find specific discussions across all your Claude Code history
- 📂 **Project organization** - Browse conversations by project with session metadata
- 💻 **Syntax highlighting** - Code blocks with proper language detection and copy buttons
- 🎨 **Modern UI** - Clean, responsive interface with dark/light theme support
- ⚡ **Fast pagination** - Handle large conversation histories efficiently
- 🔧 **Tool visualization** - Clear display of tool usage and outputs

## 🚀 Quick Start

### Installation

```bash
pip install claude-code-viewer
```

### Usage

```bash
# Start with default settings (looks for ~/.claude/projects)
claude-viewer

# Custom Claude projects path
claude-viewer --projects-path /path/to/your/claude/projects

# Custom port
claude-viewer --port 8080

# Accessible from other machines
claude-viewer --host 0.0.0.0 --port 3000
```

Then open your browser to: `http://localhost:6300`

## 📸 Screenshots

### Main Dashboard
Browse all your Claude Code projects with session counts and quick stats.

### Conversation View
View conversations with:
- Proper message formatting and line breaks
- Syntax-highlighted code blocks with copy buttons
- Tool usage visualization
- Search and filtering capabilities

## 🛠️ Command Line Options

```bash
claude-viewer --help
```

**Available options:**
- `--projects-path` - Path to Claude projects directory (default: `~/.claude/projects`)
- `--host` - Host to bind the server (default: `127.0.0.1`)
- `--port` - Port to run on (default: `6300`)
- `--version` - Show version information

## 📁 How It Works

Claude Code stores conversation history in JSONL files at `~/.claude/projects/`. This tool:

1. **Scans** your Claude projects directory
2. **Parses** JSONL conversation files
3. **Presents** them in a beautiful web interface
4. **Enables** search and filtering across all conversations

## 🔧 Development

### Local Development

```bash
git clone https://github.com/desis123/claude-code-viewer
cd claude-code-viewer
pip install -e .
claude-viewer
```

### Project Structure

```
claude-code-viewer/
├── claude_viewer/          # Main package
│   ├── cli.py             # Command line interface  
│   ├── main.py            # FastAPI application
│   └── utils/             # Utilities (JSONL parser)
├── static/                # CSS, JavaScript
├── templates/             # HTML templates
└── setup.py              # Package configuration
```

## 🤝 Contributing

Contributions welcome! Please:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
git clone <your-fork>
cd claude-code-viewer
pip install -e ".[dev]"
```

## 📋 Requirements

- **Python 3.8+**
- **Claude Code** (to generate conversation history)
- **Modern web browser**

## 🐛 Troubleshooting

### "Projects path does not exist"
Make sure Claude Code has been used and has created conversation files. The default path is `~/.claude/projects`.

### "No JSONL files found"
Ensure you have used Claude Code and it has generated conversation history. Try specifying a custom path with `--projects-path`.

### Port already in use
Use a different port: `claude-viewer --port 8080`

## 📄 License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Bootstrap](https://getbootstrap.com/)
- Syntax highlighting by [Pygments](https://pygments.org/)
- Created for the Claude Code community

## 📊 Stats

- 🎯 **Zero configuration** for most users
- ⚡ **Sub-second startup** time
- 🔍 **Full-text search** across all conversations
- 📱 **Mobile responsive** design

---

**Made with ❤️ for the Claude Code community**

[Report Issues](https://github.com/desis123/claude-code-viewer/issues) • [Feature Requests](https://github.com/desis123/claude-code-viewer/issues/new)