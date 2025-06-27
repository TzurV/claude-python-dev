# Python Project MCP Service 🐍

A powerful Model Context Protocol (MCP) service that enables Claude to intelligently explore, understand, and analyze Python projects. This service provides Claude with comprehensive tools to navigate codebases, analyze dependencies, search code patterns, and understand project structure automatically.

## 🚀 Features

- **Intelligent Project Discovery**: Automatically identifies Python projects and their structure
- **Comprehensive Code Analysis**: Reads and analyzes Python files, configurations, and documentation
- **Dependency Mapping**: Extracts and analyzes dependencies from various requirement files
- **Smart Code Search**: Pattern-based searching across your entire codebase
- **Project Structure Visualization**: Interactive directory tree exploration
- **Resource Management**: Efficient handling of large codebases with smart filtering

## 📋 Prerequisites

- Python 3.8 or higher
- Poetry (recommended) or pip for dependency management
- Claude Desktop application

## 🛠️ Installation

### Using Poetry (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/python-project-mcp
   cd python-project-mcp
   ```

2. **Initialize Poetry and configure virtual environment**:
   ```bash
   poetry init
   poetry config virtualenvs.in-project true
   poetry env use python  # or specify your Python path
   ```

3. **Install dependencies**:
   ```bash
   poetry add mcp
   ```

### Using pip

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/python-project-mcp
   cd python-project-mcp
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate.bat
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install mcp
   ```

## ⚙️ Configuration

### Claude Desktop Setup

1. **Locate your Claude Desktop config file**:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Add the MCP server configuration**:

   **Using Poetry (Recommended)**:
   ```json
   {
     "mcpServers": {
       "python-project": {
         "command": "cmd",
         "args": ["/c", "cd /d C:\\path\\to\\your\\project && poetry run python python_project_mcp.py"]
       }
     }
   }
   ```

   **Using Direct Python Path**:
   ```json
   {
     "mcpServers": {
       "python-project": {
         "command": "/path/to/your/project/.venv/bin/python",
         "args": ["/path/to/your/project/python_project_mcp.py"]
       }
     }
   }
   ```

   **Platform-specific examples**:
   
   **Windows with Poetry**:
   ```json
   {
     "mcpServers": {
       "python-project": {
         "command": "cmd",
         "args": ["/c", "cd /d C:\\Users\\YourUsername\\Projects\\python-project-mcp && poetry run python python_project_mcp.py"]
       }
     }
   }
   ```

   **Windows with Direct Path**:
   ```json
   {
     "mcpServers": {
       "python-project": {
         "command": "C:\\Users\\YourUsername\\Projects\\python-project-mcp\\.venv\\Scripts\\python.exe",
         "args": ["C:\\Users\\YourUsername\\Projects\\python-project-mcp\\python_project_mcp.py"]
       }
     }
   }
   ```

   **macOS/Linux with Poetry**:
   ```json
   {
     "mcpServers": {
       "python-project": {
         "command": "bash",
         "args": ["-c", "cd /Users/yourusername/projects/python-project-mcp && poetry run python python_project_mcp.py"]
       }
     }
   }
   ```

   **macOS/Linux with Direct Path**:
   ```json
   {
     "mcpServers": {
       "python-project": {
         "command": "/Users/yourusername/projects/python-project-mcp/.venv/bin/python",
         "args": ["/Users/yourusername/projects/python-project-mcp/python_project_mcp.py"]
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the new MCP service.

## 🧪 Testing the Installation

### Local Testing

Before configuring with Claude, test the service locally:

**Using Poetry (Recommended)**:
```bash
# Navigate to your project directory
cd /path/to/your/project

# Run the service with Poetry
poetry run python python_project_mcp.py
```

**Using Virtual Environment**:
```bash
# Activate your virtual environment
.venv\Scripts\activate.bat  # Windows
# or
source .venv/bin/activate   # macOS/Linux

# Run the service
python python_project_mcp.py
```

The service should start and wait for MCP protocol messages.

### Testing with Claude

1. Open Claude Desktop
2. Start a new conversation
3. Try the following command to verify the service is working:
   ```
   Set the project root to "/Users/yourusername/projects/your-python-project"
   ```
   
   **Example paths**:
   - Windows: `"C:\Users\YourUsername\Projects\MyPythonApp"`
   - macOS: `"/Users/yourusername/projects/my-python-app"`
   - Linux: `"/home/yourusername/projects/my-python-app"`

If successful, Claude will confirm the project root is set and show Python project indicators found.

## 🎯 Usage Examples

### Basic Project Analysis

```
Set the project root to "/Users/yourusername/projects/my-python-app"
```

### Explore Project Structure

```
Show me the project structure with a maximum depth of 3 levels
```

### Find Python Files

```
Find all Python files in the project, excluding test files
```

### Analyze Dependencies

```
Analyze the project dependencies including import statements
```

### Search Code Patterns

```
Search for "async def" in all Python files
```

### Read Specific Files

```
Read the contents of main.py
```

### Get Comprehensive Project Overview

```
Get complete project information and overview
```

## 🔧 Available Tools

The service provides Claude with the following tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `set_project_root` | Set the root directory of the Python project | `path` (string) |
| `explore_project_structure` | Get project structure overview | `max_depth` (int), `include_hidden` (bool) |
| `read_file` | Read contents of a specific file | `file_path` (string) |
| `find_python_files` | Find Python files with optional filtering | `pattern` (string), `include_tests` (bool) |
| `analyze_dependencies` | Analyze project dependencies and imports | `include_imports` (bool) |
| `search_code` | Search for patterns within Python files | `query` (string), `case_sensitive` (bool), `file_pattern` (string) |
| `get_project_info` | Get comprehensive project information | None |

## 📁 Supported File Types

- **Python Files**: `.py`, `.pyx`, `.pyi`
- **Configuration Files**: `.toml`, `.cfg`, `.ini`, `.yaml`, `.yml`, `.json`
- **Documentation**: `.md`, `.rst`, `.txt`
- **Requirements**: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`, `Pipfile`

## 🎨 Smart Features

### Automatic Project Detection

The service automatically identifies Python projects by looking for:
- Python files in the root directory
- Common Python project files (`requirements.txt`, `pyproject.toml`, etc.)
- Python packages (directories with `__init__.py`)

### Intelligent Filtering

- Automatically excludes common build/cache directories (`__pycache__`, `.git`, `node_modules`, etc.)
- Handles large files gracefully (1MB limit with informative errors)
- Supports both hidden and visible file exploration

### Dependency Analysis

- Parses multiple requirement file formats
- Analyzes import statements across the codebase
- Provides usage statistics for imported modules

## 📊 Example Analysis: This Project

Here's what the service discovers when analyzing itself:

### Project Structure
```
📁 python-project-mcp/
  🐍 python_project_mcp.py (15.2KB)
  📦 pyproject.toml (1.2KB)
  📝 README.md (8.5KB)
  📄 .gitignore (0.8KB)
  📁 .venv/
    📁 lib/
    📁 Scripts/
```

### Dependencies Found
- **From pyproject.toml**: `mcp`
- **From imports analysis**: `asyncio`, `json`, `logging`, `os`, `sys`, `pathlib`, `typing`

### Key Capabilities Demonstrated
- **7 MCP tools** for comprehensive project analysis
- **500+ lines** of well-structured Python code
- **Async/await patterns** for efficient I/O operations
- **Robust error handling** throughout the codebase
- **Comprehensive logging** for debugging and monitoring

### Code Patterns Found
- **15 async functions** for non-blocking operations
- **Multiple file parsers** for different configuration formats
- **Smart filtering logic** to handle large codebases efficiently
- **Resource management** with proper cleanup and limits

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Troubleshooting

### Common Issues

1. **Service not appearing in Claude**: Ensure the path in `claude_desktop_config.json` is correct and Claude Desktop has been restarted.

2. **Permission errors**: Make sure the Python executable and script have proper permissions.

3. **Module import errors**: Verify that the virtual environment is properly activated and MCP is installed.

4. **Large file errors**: The service has a 1MB file size limit. For larger files, consider using the search functionality instead.

### Debug Mode

To enable debug logging, modify the logging level in the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🌟 Why This MCP Service?

This service transforms how Claude interacts with Python projects by providing:

- **Instant Project Understanding**: Claude can immediately grasp your project structure
- **Intelligent Code Navigation**: No more manually copying/pasting code snippets
- **Comprehensive Analysis**: From dependencies to code patterns, get the full picture
- **Efficient Workflow**: Ask natural language questions about your codebase
- **Smart Filtering**: Focus on what matters while excluding noise

Perfect for code reviews, refactoring assistance, documentation generation, and learning new codebases!

---

Made with ❤️ for the Claude and Python communities