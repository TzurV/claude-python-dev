#!/usr/bin/env python3
"""
Python Project MCP Service

This MCP service provides tools for Claude to explore and understand Python projects
by automatically discovering project structure, reading source files, and analyzing
dependencies and configurations.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File extensions to include for different file types
PYTHON_EXTENSIONS = {'.py', '.pyx', '.pyi'}
CONFIG_EXTENSIONS = {'.toml', '.cfg', '.ini', '.yaml', '.yml', '.json'}
DOC_EXTENSIONS = {'.md', '.rst', '.txt'}
REQUIREMENTS_FILES = {'requirements.txt', 'requirements-dev.txt', 'pyproject.toml', 'setup.py', 'setup.cfg', 'Pipfile'}

# Directories to exclude from exploration
EXCLUDE_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', '.bzr',
    '.tox', '.pytest_cache', '.mypy_cache', '.coverage',
    'node_modules', '.venv', 'venv', 'env', '.env',
    'build', 'dist', '.egg-info', '.eggs', 'htmlcov'
}

# Maximum file size to read (in bytes)
MAX_FILE_SIZE = 1024 * 1024  # 1MB

class PythonProjectMCP:
    def __init__(self):
        self.server = Server("python-project")
        self.root_directory: Optional[Path] = None
        
        # Register tools
        self._register_tools()
        self._register_handlers()
    
    def _register_tools(self):
        """Register all available tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="set_project_root",
                    description="Set the root directory of the Python project to analyze",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the project root directory"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="explore_project_structure",
                    description="Get an overview of the project structure including directories and key files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum directory depth to explore (default: 3)",
                                "default": 3
                            },
                            "include_hidden": {
                                "type": "boolean",
                                "description": "Include hidden files and directories (default: false)",
                                "default": False
                            }
                        }
                    }
                ),
                types.Tool(
                    name="read_file",
                    description="Read the contents of a specific file in the project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file relative to project root or absolute path"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                types.Tool(
                    name="find_python_files",
                    description="Find all Python files in the project with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Optional filename pattern to match (supports wildcards)"
                            },
                            "include_tests": {
                                "type": "boolean",
                                "description": "Include test files (default: true)",
                                "default": True
                            }
                        }
                    }
                ),
                types.Tool(
                    name="analyze_dependencies",
                    description="Analyze project dependencies from requirements files and imports",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_imports": {
                                "type": "boolean",
                                "description": "Analyze import statements in Python files (default: true)",
                                "default": True
                            }
                        }
                    }
                ),
                types.Tool(
                    name="search_code",
                    description="Search for specific patterns or text within Python files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Text or pattern to search for"
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "Whether search should be case sensitive (default: false)",
                                "default": False
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "Optional file pattern to limit search scope"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="get_project_info",
                    description="Get comprehensive project information including structure, dependencies, and metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            try:
                if name == "set_project_root":
                    return await self._set_project_root(arguments.get("path"))
                elif name == "explore_project_structure":
                    return await self._explore_project_structure(
                        arguments.get("max_depth", 3),
                        arguments.get("include_hidden", False)
                    )
                elif name == "read_file":
                    return await self._read_file(arguments.get("file_path"))
                elif name == "find_python_files":
                    return await self._find_python_files(
                        arguments.get("pattern"),
                        arguments.get("include_tests", True)
                    )
                elif name == "analyze_dependencies":
                    return await self._analyze_dependencies(
                        arguments.get("include_imports", True)
                    )
                elif name == "search_code":
                    return await self._search_code(
                        arguments.get("query"),
                        arguments.get("case_sensitive", False),
                        arguments.get("file_pattern")
                    )
                elif name == "get_project_info":
                    return await self._get_project_info()
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _register_handlers(self):
        """Register initialization and other handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List available resources"""
            if not self.root_directory:
                return []
            
            resources = []
            try:
                # Add project overview resource
                resources.append(types.Resource(
                    uri=f"project://overview",
                    name="Project Overview",
                    description="Complete overview of the Python project structure and metadata",
                    mimeType="text/plain"
                ))
                
                # Add Python files as resources
                for py_file in self._get_python_files():
                    rel_path = py_file.relative_to(self.root_directory)
                    resources.append(types.Resource(
                        uri=f"file://{rel_path}",
                        name=str(rel_path),
                        description=f"Python source file: {rel_path}",
                        mimeType="text/x-python"
                    ))
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a specific resource"""
            if not self.root_directory:
                raise ValueError("No project root set")
            
            if uri == "project://overview":
                return await self._generate_project_overview()
            elif uri.startswith("file://"):
                file_path = uri[7:]  # Remove "file://" prefix
                full_path = self.root_directory / file_path
                return self._read_file_content(full_path)
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
    
    async def _set_project_root(self, path: str) -> list[types.TextContent]:
        """Set the project root directory"""
        try:
            root_path = Path(path).resolve()
            if not root_path.exists():
                return [types.TextContent(type="text", text=f"Error: Path does not exist: {path}")]
            if not root_path.is_dir():
                return [types.TextContent(type="text", text=f"Error: Path is not a directory: {path}")]
            
            self.root_directory = root_path
            
            # Validate it looks like a Python project
            python_indicators = self._find_python_indicators()
            
            response = f"Project root set to: {self.root_directory}\n\n"
            if python_indicators:
                response += "Python project indicators found:\n"
                for indicator in python_indicators:
                    response += f"  - {indicator}\n"
            else:
                response += "Warning: No clear Python project indicators found in this directory."
            
            return [types.TextContent(type="text", text=response)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error setting project root: {e}")]
    
    def _find_python_indicators(self) -> List[str]:
        """Find indicators that this is a Python project"""
        if not self.root_directory:
            return []
        
        indicators = []
        
        # Check for Python files
        python_files = list(self.root_directory.glob("*.py"))
        if python_files:
            indicators.append(f"{len(python_files)} Python files in root")
        
        # Check for common Python project files
        for file_name in REQUIREMENTS_FILES:
            if (self.root_directory / file_name).exists():
                indicators.append(f"Found {file_name}")
        
        # Check for Python packages (directories with __init__.py)
        packages = [d for d in self.root_directory.iterdir() 
                   if d.is_dir() and (d / "__init__.py").exists()]
        if packages:
            indicators.append(f"{len(packages)} Python packages found")
        
        return indicators
    
    async def _explore_project_structure(self, max_depth: int, include_hidden: bool) -> list[types.TextContent]:
        """Explore and return project structure"""
        if not self.root_directory:
            return [types.TextContent(type="text", text="Error: No project root set")]
        
        try:
            structure = self._build_directory_tree(self.root_directory, max_depth, include_hidden)
            return [types.TextContent(type="text", text=structure)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error exploring structure: {e}")]
    
    def _build_directory_tree(self, path: Path, max_depth: int, include_hidden: bool, current_depth: int = 0) -> str:
        """Build a text representation of directory structure"""
        if current_depth >= max_depth:
            return ""
        
        tree_lines = []
        indent = "  " * current_depth
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                # Skip hidden files/dirs unless requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                # Skip excluded directories
                if item.is_dir() and item.name in EXCLUDE_DIRS:
                    continue
                
                if item.is_dir():
                    tree_lines.append(f"{indent}📁 {item.name}/")
                    if current_depth < max_depth - 1:
                        subtree = self._build_directory_tree(item, max_depth, include_hidden, current_depth + 1)
                        if subtree:
                            tree_lines.append(subtree)
                else:
                    icon = self._get_file_icon(item)
                    size = self._format_file_size(item.stat().st_size)
                    tree_lines.append(f"{indent}{icon} {item.name} ({size})")
        
        except PermissionError:
            tree_lines.append(f"{indent}❌ Permission denied")
        
        return "\n".join(tree_lines)
    
    def _get_file_icon(self, file_path: Path) -> str:
        """Get appropriate icon for file type"""
        suffix = file_path.suffix.lower()
        if suffix in PYTHON_EXTENSIONS:
            return "🐍"
        elif suffix in CONFIG_EXTENSIONS:
            return "⚙️"
        elif suffix in DOC_EXTENSIONS:
            return "📝"
        elif file_path.name in REQUIREMENTS_FILES:
            return "📦"
        else:
            return "📄"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    async def _read_file(self, file_path: str) -> list[types.TextContent]:
        """Read contents of a specific file"""
        if not self.root_directory:
            return [types.TextContent(type="text", text="Error: No project root set")]
        
        try:
            # Handle both relative and absolute paths
            path = Path(file_path)
            if not path.is_absolute():
                path = self.root_directory / path
            
            content = self._read_file_content(path)
            return [types.TextContent(type="text", text=f"File: {path.relative_to(self.root_directory)}\n\n{content}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error reading file: {e}")]
    
    def _read_file_content(self, file_path: Path) -> str:
        """Read file content with error handling"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.stat().st_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_path} ({self._format_file_size(file_path.stat().st_size)})")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _get_python_files(self) -> List[Path]:
        """Get all Python files in the project"""
        if not self.root_directory:
            return []
        
        python_files = []
        for ext in PYTHON_EXTENSIONS:
            python_files.extend(self.root_directory.rglob(f"*{ext}"))
        
        # Filter out files in excluded directories
        filtered_files = []
        for file_path in python_files:
            if not any(part in EXCLUDE_DIRS for part in file_path.parts):
                filtered_files.append(file_path)
        
        return sorted(filtered_files)
    
    async def _find_python_files(self, pattern: Optional[str], include_tests: bool) -> list[types.TextContent]:
        """Find Python files with optional filtering"""
        if not self.root_directory:
            return [types.TextContent(type="text", text="Error: No project root set")]
        
        try:
            python_files = self._get_python_files()
            
            # Apply pattern filter if provided
            if pattern:
                import fnmatch
                python_files = [f for f in python_files if fnmatch.fnmatch(f.name, pattern)]
            
            # Filter out test files if requested
            if not include_tests:
                python_files = [f for f in python_files 
                              if not any(part.startswith('test') for part in f.parts)]
            
            if not python_files:
                return [types.TextContent(type="text", text="No Python files found matching criteria")]
            
            result = f"Found {len(python_files)} Python files:\n\n"
            for file_path in python_files:
                rel_path = file_path.relative_to(self.root_directory)
                size = self._format_file_size(file_path.stat().st_size)
                result += f"  🐍 {rel_path} ({size})\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error finding Python files: {e}")]
    
    async def _analyze_dependencies(self, include_imports: bool) -> list[types.TextContent]:
        """Analyze project dependencies"""
        if not self.root_directory:
            return [types.TextContent(type="text", text="Error: No project root set")]
        
        try:
            result = "Project Dependencies Analysis\n" + "="*35 + "\n\n"
            
            # Analyze requirements files
            deps_from_files = self._analyze_requirement_files()
            if deps_from_files:
                result += "Dependencies from requirements files:\n"
                for file_name, deps in deps_from_files.items():
                    result += f"\n{file_name}:\n"
                    for dep in deps[:10]:  # Limit to first 10
                        result += f"  - {dep}\n"
                    if len(deps) > 10:
                        result += f"  ... and {len(deps) - 10} more\n"
            
            # Analyze imports if requested
            if include_imports:
                imports = self._analyze_imports()
                if imports:
                    result += f"\nImported modules (top 20):\n"
                    sorted_imports = sorted(imports.items(), key=lambda x: x[1], reverse=True)
                    for module, count in sorted_imports[:20]:
                        result += f"  - {module} (used {count} times)\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error analyzing dependencies: {e}")]
    
    def _analyze_requirement_files(self) -> Dict[str, List[str]]:
        """Analyze requirements from various requirement files"""
        results = {}
        
        for req_file in REQUIREMENTS_FILES:
            file_path = self.root_directory / req_file
            if file_path.exists():
                try:
                    if req_file.endswith('.txt'):
                        deps = self._parse_requirements_txt(file_path)
                    elif req_file == 'pyproject.toml':
                        deps = self._parse_pyproject_toml(file_path)
                    elif req_file in ['setup.py', 'setup.cfg']:
                        deps = self._parse_setup_file(file_path)
                    else:
                        continue
                    
                    if deps:
                        results[req_file] = deps
                except Exception as e:
                    logger.warning(f"Error parsing {req_file}: {e}")
        
        return results
    
    def _parse_requirements_txt(self, file_path: Path) -> List[str]:
        """Parse requirements.txt style files"""
        deps = []
        content = self._read_file_content(file_path)
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                deps.append(line.split()[0])  # Take first part before any options
        return deps
    
    def _parse_pyproject_toml(self, file_path: Path) -> List[str]:
        """Parse pyproject.toml for dependencies"""
        deps = []
        content = self._read_file_content(file_path)
        
        # Simple parsing - look for dependencies sections
        in_deps_section = False
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('[tool.poetry.dependencies]') or line.startswith('dependencies = ['):
                in_deps_section = True
                continue
            elif line.startswith('[') and in_deps_section:
                in_deps_section = False
            elif in_deps_section and '=' in line:
                dep_name = line.split('=')[0].strip().strip('"\'')
                if dep_name != 'python':
                    deps.append(dep_name)
        
        return deps
    
    def _parse_setup_file(self, file_path: Path) -> List[str]:
        """Extract dependencies from setup.py/setup.cfg"""
        # This is a simplified parser - in practice you might want more robust parsing
        deps = []
        content = self._read_file_content(file_path)
        
        # Look for install_requires or similar patterns
        import re
        patterns = [
            r'install_requires\s*=\s*\[(.*?)\]',
            r'requires\s*=\s*\[(.*?)\]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                # Extract package names from strings
                package_strings = re.findall(r'["\']([^"\']+)["\']', match)
                for pkg in package_strings:
                    deps.append(pkg.split('>=')[0].split('==')[0].split('<')[0].strip())
        
        return deps
    
    def _analyze_imports(self) -> Dict[str, int]:
        """Analyze import statements in Python files"""
        import_counts = {}
        python_files = self._get_python_files()
        
        import re
        import_patterns = [
            r'^import\s+([^\s,]+)',
            r'^from\s+([^\s,]+)\s+import',
        ]
        
        for file_path in python_files:
            try:
                content = self._read_file_content(file_path)
                for line in content.split('\n'):
                    line = line.strip()
                    for pattern in import_patterns:
                        match = re.match(pattern, line)
                        if match:
                            module = match.group(1).split('.')[0]  # Get top-level module
                            import_counts[module] = import_counts.get(module, 0) + 1
            except Exception as e:
                logger.warning(f"Error analyzing imports in {file_path}: {e}")
        
        return import_counts
    
    async def _search_code(self, query: str, case_sensitive: bool, file_pattern: Optional[str]) -> list[types.TextContent]:
        """Search for patterns in Python files"""
        if not self.root_directory:
            return [types.TextContent(type="text", text="Error: No project root set")]
        
        try:
            python_files = self._get_python_files()
            
            # Apply file pattern filter if provided
            if file_pattern:
                import fnmatch
                python_files = [f for f in python_files if fnmatch.fnmatch(f.name, file_pattern)]
            
            matches = []
            for file_path in python_files:
                try:
                    content = self._read_file_content(file_path)
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        search_line = line if case_sensitive else line.lower()
                        search_query = query if case_sensitive else query.lower()
                        
                        if search_query in search_line:
                            rel_path = file_path.relative_to(self.root_directory)
                            matches.append({
                                'file': str(rel_path),
                                'line': line_num,
                                'content': line.strip()
                            })
                except Exception as e:
                    logger.warning(f"Error searching in {file_path}: {e}")
            
            if not matches:
                return [types.TextContent(type="text", text=f"No matches found for '{query}'")]
            
            result = f"Found {len(matches)} matches for '{query}':\n\n"
            for match in matches[:50]:  # Limit to first 50 matches
                result += f"{match['file']}:{match['line']}: {match['content']}\n"
            
            if len(matches) > 50:
                result += f"\n... and {len(matches) - 50} more matches"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error searching code: {e}")]
    
    async def _get_project_info(self) -> list[types.TextContent]:
        """Get comprehensive project information"""
        if not self.root_directory:
            return [types.TextContent(type="text", text="Error: No project root set")]
        
        try:
            info = await self._generate_project_overview()
            return [types.TextContent(type="text", text=info)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting project info: {e}")]
    
    async def _generate_project_overview(self) -> str:
        """Generate comprehensive project overview"""
        if not self.root_directory:
            return "No project root set"
        
        overview = f"Python Project Overview: {self.root_directory.name}\n"
        overview += "=" * (25 + len(self.root_directory.name)) + "\n\n"
        
        # Basic project info
        overview += f"📁 Project Root: {self.root_directory}\n"
        
        # Project structure summary
        python_files = self._get_python_files()
        overview += f"🐍 Python Files: {len(python_files)}\n"
        
        # Find packages
        packages = [d for d in self.root_directory.iterdir() 
                   if d.is_dir() and (d / "__init__.py").exists()]
        if packages:
            overview += f"📦 Python Packages: {len(packages)}\n"
            for pkg in packages[:5]:  # Show first 5
                overview += f"    - {pkg.name}\n"
            if len(packages) > 5:
                overview += f"    ... and {len(packages) - 5} more\n"
        
        # Configuration files
        config_files = []
        for file_name in REQUIREMENTS_FILES:
            if (self.root_directory / file_name).exists():
                config_files.append(file_name)
        
        if config_files:
            overview += f"⚙️  Configuration Files: {', '.join(config_files)}\n"
        
        # Documentation files
        doc_files = []
        for ext in DOC_EXTENSIONS:
            doc_files.extend(self.root_directory.glob(f"*{ext}"))
        
        if doc_files:
            overview += f"📝 Documentation: {len(doc_files)} files\n"
        
        # Quick dependency analysis
        deps_info = self._analyze_requirement_files()
        if deps_info:
            total_deps = sum(len(deps) for deps in deps_info.values())
            overview += f"📋 Dependencies: ~{total_deps} packages\n"
        
        overview += "\n" + "=" * 50 + "\n"
        overview += "Use other tools to explore specific aspects of the project!"
        
        return overview
    
    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="python-project",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

async def main():
    """Main entry point"""
    mcp_service = PythonProjectMCP()
    await mcp_service.run()

if __name__ == "__main__":
    asyncio.run(main())
    