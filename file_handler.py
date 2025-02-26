import os

class FileHandler:
    # Default patterns to exclude
    DEFAULT_EXCLUDE_PATTERNS = {
        'node_modules',
        'venv',
        'myenv',
        '.venv',
        '__pycache__',
        '.git',
        '.idea',
        '.vs',
        '.vscode',
        'dist',
        'build',
        'target',
        'vendor',
        '.pytest_cache',
        '.mypy_cache',
        '.next',
        'coverage',
        'env',
        '.env',
        '.env.local',
        '.gitignore'
    }

    def __init__(self, exclude_patterns=None):
        """
        Initialize FileHandler with optional custom exclude patterns.
        
        Args:
            exclude_patterns (set, optional): Custom patterns to exclude. If None, uses default patterns.
        """
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS if exclude_patterns is None else exclude_patterns
        self.visited_paths = set()  # Track visited paths to prevent cycles

    def is_safe_path(self, path):
        """
        Check if a path is safe to traverse (no symlink cycles).
        
        Args:
            path (str): Path to check
            
        Returns:
            bool: True if path is safe to traverse, False if it might create a cycle
        """
        try:
            real_path = os.path.realpath(path)  # Resolve any symlinks
            if real_path in self.visited_paths:
                return False
            self.visited_paths.add(real_path)
            return True
        except Exception:
            return False  # If we can't resolve the path, consider it unsafe

    def clear_visited_paths(self):
        """Clear the set of visited paths"""
        self.visited_paths.clear()

    def should_exclude(self, path):
        """
        Check if a path should be excluded based on exclude patterns.
        
        Args:
            path (str): Path to check
            
        Returns:
            bool: True if path should be excluded, False otherwise
        """
        path_parts = path.replace('\\', '/').split('/')
        return any(part in self.exclude_patterns for part in path_parts)

    def get_files(self, directory, extensions=None):
        """
        Get all files in the directory and its subdirectories that match the given extensions,
        excluding specified patterns.
        
        Args:
            directory (str): Directory path to search
            extensions (list, optional): List of file extensions to filter by
        
        Returns:
            list: List of matching file paths (relative to the directory)
        """
        if not os.path.exists(directory):
            raise ValueError(f"Directory '{directory}' does not exist")
            
        # Clear visited paths before starting a new traversal
        self.clear_visited_paths()
            
        files = []
        for root, dirs, filenames in os.walk(directory, followlinks=False):  # Don't follow symlinks in os.walk
            # Check if this directory is safe to traverse
            if not self.is_safe_path(root):
                print(f"Warning: Skipping potentially circular path: {root}")
                continue

            # Remove excluded directories from dirs list to prevent walking into them
            dirs[:] = [d for d in dirs if d not in self.exclude_patterns]
            
            # Get relative path from the search directory
            rel_path = os.path.relpath(root, directory)
            if rel_path == '.':
                rel_path = ''
                
            for filename in filenames:
                # Skip files in excluded directories
                if self.should_exclude(os.path.join(rel_path, filename)):
                    continue
                    
                # Check file extension if extensions filter is provided
                if extensions and not any(filename.endswith(ext) for ext in extensions):
                    continue
                    
                file_path = os.path.join(rel_path, filename)
                files.append(file_path)
        
        return sorted(files)
    
    def read_file(self, filepath):
        """
        Read the contents of a file.
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            str: Contents of the file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read file '{filepath}': {str(e)}")
