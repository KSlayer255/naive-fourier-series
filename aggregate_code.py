import fnmatch
import os
from pathlib import Path
from typing import List, Optional, Set


class ProjectStructureGenerator:
    """
    A configurable project structure and source code aggregator
    that works with any programming language or project type.
    """

    def __init__(self):
        # Core configuration - easily customizable for any project
        self.IGNORED_DIRS: Set[str] = {
            # Version control
            ".git",
            ".svn",
            ".hg",
            # Build systems
            "node_modules",
            "dist",
            "build",
            "out",
            "target",
            ".pio",
            ".vscode",
            # IDE
            ".idea",
            ".vscode",
            ".vs",
            # Environment
            ".env",
            "venv",
            ".venv",
            "env",
            "virtualenv",
            ".conda",
            # OS
            "__pycache__",
            ".pytest_cache",
            ".cache",
        }

        self.IGNORED_FILES: Set[str] = {
            # OS metadata
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini",
            # Dependency locks
            "package-lock.json",
            "yarn.lock",
            "poetry.lock",
            "Pipfile.lock",
            "composer.lock",
            "Gemfile.lock",
            "Cargo.lock",
            # Environment
            ".env",
            ".env.local",
            ".env.*.local",
            # Build outputs
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "*.so",
            "*.dll",
            "*.exe",
            # This script's outputs
            "project-structure.txt",
            "all-contents.txt",
            # The script itself
            "aggregate_code.py",
        }

        self.IGNORED_EXTENSIONS: Set[str] = {
            # Logs and temporary files
            ".log",
            ".tmp",
            ".temp",
            ".swp",
            ".swo",
            # Archives
            ".zip",
            ".tar",
            ".gz",
            ".tgz",
            ".rar",
            ".7z",
            # Binary and compiled files
            ".o",
            ".obj",
            ".class",
            ".jar",
            ".war",
            ".ear",
            ".dll",
            ".exe",
            ".so",
            ".dylib",
            ".a",
            ".lib",
        }

        # Source file detection - easily extensible
        self.SOURCE_EXTENSIONS: Set[str] = {
            # Web
            ".html",
            ".htm",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            # Backend
            ".py",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".scala",
            ".kt",
            ".swift",
            ".m",
            ".pl",
            ".r",
            ".lua",
            # Data & Config
            ".json",
            ".yaml",
            ".yml",
            ".xml",
            ".csv",
            ".sql",
            ".graphql",
            ".gql",
            ".proto",
            ".thrift",
            ".avdl",
            # Documentation
            ".md",
            ".txt",
            ".rst",
            ".tex",
            ".rdoc",
            # Build/config files
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".properties",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".dockerfile",
            "dockerfile",
            ".gitignore",
            ".gitattributes",
        }

        # Test file patterns to exclude from content aggregation
        self.TEST_FILE_PATTERNS: Set[str] = {
            "*test*",
            "*spec*",
            "*mock*",
            "*stub*",
            "*fixture*",
        }

        self.OUTPUT_FILE = "project-structure.txt"
        self.CONTENTS_FILE = "all-contents.txt"

    def should_ignore(self, file_path: str) -> bool:
        """
        Comprehensive ignore checking with pattern matching
        """
        path_obj = Path(file_path)
        basename = path_obj.name
        ext = path_obj.suffix.lower()
        parent_path = str(path_obj.parent).lower()

        # Check exact directory matches
        if basename in self.IGNORED_DIRS:
            return True

        # Check file patterns (supports wildcards)
        if any(fnmatch.fnmatch(basename, pattern) for pattern in self.IGNORED_FILES):
            return True

        # Check extensions
        if ext in self.IGNORED_EXTENSIONS:
            return True

        # Check for common patterns in path
        ignored_path_patterns = {"node_modules", "vendor", "target", "dist", "build"}
        if any(pattern in parent_path for pattern in ignored_path_patterns):
            return True

        return False

    def is_source_code_file(self, file_path: str, include_tests: bool = False) -> bool:
        """
        Flexible source file detection with test filtering
        """
        path_obj = Path(file_path)
        basename = path_obj.name.lower()
        ext = path_obj.suffix.lower()

        # Check if it has a source extension
        if ext not in self.SOURCE_EXTENSIONS:
            return False

        # Optionally exclude test files
        if not include_tests:
            if any(
                fnmatch.fnmatch(basename, pattern)
                for pattern in self.TEST_FILE_PATTERNS
            ):
                return False

        return True

    def is_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file"""
        basename = Path(file_path).name.lower()
        return any(
            fnmatch.fnmatch(basename, pattern) for pattern in self.TEST_FILE_PATTERNS
        )

    def generate_tree(
        self,
        directory: str = ".",
        prefix: str = "",
        output_stream=None,
        max_depth: Optional[int] = None,
        current_depth: int = 0,
    ) -> None:
        """
        FIXED: Enhanced tree generation with depth limiting and better formatting
        """
        if max_depth is not None and current_depth > max_depth:
            return

        try:
            entries = os.listdir(directory)

            # Filter entries and separate directories from files
            filtered_entries = []
            for entry in entries:
                entry_path = os.path.join(directory, entry)
                if not self.should_ignore(entry_path):
                    filtered_entries.append(entry)

            # Sort: directories first, then files, both alphabetically
            dirs = []
            files = []
            for entry in filtered_entries:
                entry_path = os.path.join(directory, entry)
                if os.path.isdir(entry_path):
                    dirs.append(entry)
                else:
                    files.append(entry)

            sorted_entries = sorted(dirs) + sorted(files)

            for index, entry in enumerate(sorted_entries):
                is_last = index == len(sorted_entries) - 1
                entry_path = os.path.join(directory, entry)

                try:
                    is_directory = os.path.isdir(entry_path)

                    # Add indicators for file types
                    indicator = ""
                    if is_directory:
                        indicator = "/"
                    elif self.is_test_file(entry_path):
                        indicator = " 🧪"
                    elif self.is_source_code_file(entry_path):
                        indicator = " 📄"

                    line = f"{prefix}{'└── ' if is_last else '├── '}{entry}{indicator}"

                    print(line)
                    if output_stream:
                        output_stream.write(line + "\n")

                    # RECURSION FIX: Only recurse into directories that aren't ignored
                    if is_directory:
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        self.generate_tree(
                            entry_path,
                            new_prefix,
                            output_stream,
                            max_depth,
                            current_depth + 1,
                        )

                except (OSError, PermissionError) as error:
                    self._log_error(f"Error reading {entry_path}", error, output_stream)

        except (OSError, PermissionError) as error:
            self._log_error(
                f"Error reading directory {directory}", error, output_stream
            )

    def generate_file_list(
        self,
        directory: str = ".",
        file_list: Optional[List[str]] = None,
        include_tests: bool = False,
        extensions: Optional[Set[str]] = None,
    ) -> List[str]:
        """
        FIXED: Flexible file collection with proper recursion
        """
        if file_list is None:
            file_list = []

        if extensions is None:
            extensions = self.SOURCE_EXTENSIONS

        try:
            entries = os.listdir(directory)

            for entry in entries:
                entry_path = os.path.join(directory, entry)

                if self.should_ignore(entry_path):
                    continue

                if os.path.isdir(entry_path):
                    # Recurse into directory
                    self.generate_file_list(
                        entry_path, file_list, include_tests, extensions
                    )
                else:
                    # Custom extension filter or default source detection
                    if extensions:
                        ext = Path(entry_path).suffix.lower()
                        if ext in extensions and (
                            include_tests or not self.is_test_file(entry_path)
                        ):
                            file_list.append(entry_path)
                    else:
                        if self.is_source_code_file(entry_path, include_tests):
                            file_list.append(entry_path)

        except (OSError, PermissionError) as error:
            print(f"Error reading directory {directory}: {error}")

        return file_list

    def analyze_project(self, directory: str = ".") -> dict:
        """
        Generate project statistics and analysis
        """
        all_files = self.generate_file_list(directory, include_tests=True)

        analysis = {
            "total_files": len(all_files),
            "by_extension": {},
            "test_files": 0,
            "source_files": 0,
            "largest_file": ("", 0),
            "total_directories": 0,
        }

        # Count directories by walking the tree
        dir_count = 0
        for root, dirs, files in os.walk(directory):
            # Filter out ignored directories in-place
            dirs[:] = [d for d in dirs if not self.should_ignore(os.path.join(root, d))]
            dir_count += len(dirs)

        analysis["total_directories"] = dir_count

        for file_path in all_files:
            path_obj = Path(file_path)
            ext = path_obj.suffix.lower()

            # Count by extension
            analysis["by_extension"][ext] = analysis["by_extension"].get(ext, 0) + 1

            # Count test files
            if self.is_test_file(file_path):
                analysis["test_files"] += 1
            else:
                analysis["source_files"] += 1

            # Find largest file
            try:
                size = os.path.getsize(file_path)
                if size > analysis["largest_file"][1]:
                    analysis["largest_file"] = (file_path, size)
            except OSError:
                pass

        return analysis

    def copy_file_contents(
        self, file_list: List[str], output_path: str, include_analysis: bool = False
    ) -> None:
        """
        Enhanced content aggregation with optional project analysis
        """
        with open(output_path, "w", encoding="utf-8") as output_file:
            # Header with optional analysis
            output_file.write("=== PROJECT SOURCE CODE CONTENTS ===\n")
            output_file.write("=" * 80 + "\n\n")

            if include_analysis:
                analysis = self.analyze_project()
                output_file.write("PROJECT ANALYSIS:\n")
                output_file.write(
                    f"- Total directories: {analysis['total_directories']}\n"
                )
                output_file.write(f"- Total files: {analysis['total_files']}\n")
                output_file.write(f"- Source files: {analysis['source_files']}\n")
                output_file.write(f"- Test files: {analysis['test_files']}\n")
                output_file.write(
                    f"- Largest file: {analysis['largest_file'][0]} ({analysis['largest_file'][1]} bytes)\n"
                )
                output_file.write("\nFILE EXTENSIONS:\n")
                for ext, count in sorted(analysis["by_extension"].items()):
                    output_file.write(f"- {ext or 'no extension'}: {count}\n")
                output_file.write("\n" + "=" * 80 + "\n\n")

            # File contents
            for file_path in file_list:
                output_file.write("=" * 80 + "\n")
                output_file.write(f"FILE: {file_path}\n")
                output_file.write("=" * 80 + "\n\n")

                try:
                    with open(file_path, "r", encoding="utf-8") as source_file:
                        content = source_file.read()
                        output_file.write(content)

                    output_file.write("\n\n")
                    print(f"Added: {file_path}")

                except (OSError, PermissionError, UnicodeDecodeError) as error:
                    print(f"Error reading {file_path}: {error}")
                    output_file.write(f"[Error reading file: {error}]\n\n")

    def write_tree_to_file(
        self, output_path: str, max_depth: Optional[int] = None
    ) -> None:
        """Write tree structure to file with optional depth limiting"""
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write("PROJECT STRUCTURE ANALYSIS\n")
            output_file.write("=" * 25 + "\n\n")

            # Add project analysis
            analysis = self.analyze_project()
            output_file.write("Summary:\n")
            output_file.write(f"- Total directories: {analysis['total_directories']}\n")
            output_file.write(f"- Total files: {analysis['total_files']}\n")
            output_file.write(f"- Source files: {analysis['source_files']}\n")
            output_file.write(f"- Test files: {analysis['test_files']}\n\n")

            output_file.write("Structure:\n")
            self.generate_tree(".", "", output_file, max_depth)

    def _log_error(self, message: str, error: Exception, output_stream=None) -> None:
        """Centralized error logging"""
        error_msg = f"{message}: {error}"
        print(error_msg)
        if output_stream:
            output_stream.write(error_msg + "\n")

    def run_analysis(
        self,
        include_tests: bool = False,
        specific_extensions: Optional[Set[str]] = None,
        max_depth: Optional[int] = None,
        include_project_analysis: bool = True,
    ) -> None:
        """
        Main execution with flexible configuration
        """
        print("PROJECT STRUCTURE ANALYZER")
        print("=" * 25)

        # Generate and display tree
        self.generate_tree(".", max_depth=max_depth)

        # Save tree to file
        self.write_tree_to_file(self.OUTPUT_FILE, max_depth)

        # Generate file list based on configuration
        print("\nGenerating project contents...")

        file_list = self.generate_file_list(
            include_tests=include_tests, extensions=specific_extensions
        )

        file_list.sort()

        print(f"Found {len(file_list)} files matching criteria")

        # Copy contents with optional analysis
        self.copy_file_contents(file_list, self.CONTENTS_FILE, include_project_analysis)

        # Final summary
        print(f"\n✅ Analysis complete!")
        print(f"📁 Structure: {self.OUTPUT_FILE}")
        print(f"📄 Contents: {self.CONTENTS_FILE}")


# Simplified usage for common cases
def quick_analysis(extensions: Optional[Set[str]] = None, include_tests: bool = False):
    """Quick one-liner for common use cases"""
    generator = ProjectStructureGenerator()
    generator.run_analysis(
        include_tests=include_tests,
        specific_extensions=extensions,
        include_project_analysis=True,
    )


# Test the tree generation
def test_tree_generation():
    """Test function to verify the tree generation works"""
    print("=== TESTING TREE GENERATION ===")
    generator = ProjectStructureGenerator()

    # Test with a small depth limit to see the structure
    generator.generate_tree(".", max_depth=2)


# Usage examples
def main():
    generator = ProjectStructureGenerator()

    # # First test the tree generation
    # test_tree_generation()

    # print("\n" + "="*50 + "\n")

    # # Example 1: Full analysis (default)
    # print("=== FULL PROJECT ANALYSIS ===")
    # generator.run_analysis()

    # Example 2: C++ specific analysis
    print("\n=== Python ONLY ANALYSIS ===")
    generator.run_analysis(
        specific_extensions={".py"}, include_tests=False, max_depth=4
    )


if __name__ == "__main__":
    main()

