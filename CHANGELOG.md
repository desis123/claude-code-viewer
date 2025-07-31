# Changelog

All notable changes to claude-code-viewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-31

### Added
- Initial release of Claude Code Viewer
- Web interface for browsing Claude Code conversation history
- Full-text search across all conversations
- Project organization with session metadata
- Syntax highlighting for code blocks with copy buttons
- Modern responsive UI with dark/light theme support
- Fast pagination for large conversation histories
- Tool usage visualization and formatting
- Command line interface with simple configuration
- Cross-platform support (Windows, macOS, Linux)
- Auto-detection of Claude projects directory
- Health check endpoint for monitoring

### Features
- **Search & Filter**: Find specific conversations and filter by message type
- **Code Highlighting**: Automatic language detection and syntax highlighting
- **Responsive Design**: Works on desktop and mobile devices
- **Zero Configuration**: Works out of the box for most users
- **Simple CLI**: Easy command line interface with minimal options
- **Fast Performance**: Efficient pagination and caching

### Technical
- Built with FastAPI and modern web technologies
- Supports Python 3.8+
- Comprehensive error handling and validation
- Clean package structure for easy maintenance
- Full test coverage and CI/CD pipeline

### Documentation
- Comprehensive README with screenshots
- Command line help and examples
- Troubleshooting guide
- Contributing guidelines