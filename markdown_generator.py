import os

class MarkdownGenerator:
    def get_language_identifier(self, filename):
        """
        Get the language identifier for code blocks based on file extension.

        Args:
            filename (str): Name of the file

        Returns:
            str: Language identifier for markdown code blocks
        """
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.md': 'markdown',
            '.json': 'json',
            '.xml': 'xml',
            '.sql': 'sql',
            '.sh': 'bash',
            '.cpp': 'cpp',
            '.c': 'c',
            '.java': 'java',
        }

        _, ext = os.path.splitext(filename)
        return extension_map.get(ext.lower(), '')

    def generate_markdown(self, file_paths, output_path):
        """
        Generate a markdown file combining the contents of selected files.

        Args:
            file_paths (list): List of file paths to combine
            output_path (str): Path where to save the markdown file
        """
        print("\n=== Starting Markdown File Generation ===")
        print(f"Output path: {output_path}")
        print(f"Number of files to process: {len(file_paths)}")
        
        try:
            # Find the common root directory for all files
            if len(file_paths) > 0:
                # Get the directory that was originally selected
                common_prefix = os.path.commonpath([os.path.dirname(p) for p in file_paths])
                
                # Find the repository root (go up until we find a .git folder or reach filesystem root)
                repo_root = common_prefix
                while repo_root and not os.path.exists(os.path.join(repo_root, '.git')):
                    parent = os.path.dirname(repo_root)
                    # Stop if we've reached the filesystem root
                    if parent == repo_root:
                        break
                    repo_root = parent
                    
                # If we couldn't find a .git folder, use the common prefix
                if not os.path.exists(os.path.join(repo_root, '.git')):
                    repo_root = common_prefix
                    
                print(f"Repository root: {repo_root}")
            else:
                common_prefix = ""
                repo_root = ""
                
            print(f"Common prefix path: {common_prefix}")
            
            # Get exclude patterns from file handler
            exclude_patterns = getattr(self, 'exclude_patterns', None)
            
            with open(output_path, 'w', encoding='utf-8') as out_file:
                # Generate and write directory tree at the beginning
                if repo_root:
                    print("Generating directory tree...")
                    tree_content = self.generate_directory_tree(repo_root, exclude_patterns)
                    out_file.write(tree_content)
                    out_file.write("\n\n# Selected Files\n\n")
                    print("Directory tree added to markdown")
                
                # Continue with existing file content logic
                for file_path in file_paths:
                    print(f"\nProcessing file: {file_path}")
                    
                    # Skip directories
                    if os.path.isdir(file_path):
                        print("  Skipping: Is a directory")
                        continue
                        
                    # Get relative path from common prefix
                    rel_path = os.path.relpath(file_path, common_prefix)
                    print(f"  Relative path: {rel_path}")
                    
                    language = self.get_language_identifier(file_path)
                    print(f"  Language: {language}")

                    # Write file header with relative path
                    out_file.write(f"# {rel_path}\n\n")
                    print("  Wrote header")

                    # Read and write file contents
                    try:
                        with open(file_path, 'r', encoding='utf-8') as in_file:
                            content = in_file.read()
                            out_file.write(f"```{language}\n{content}\n```\n\n")
                            print("  Successfully wrote content")
                    except FileNotFoundError:
                        error_msg = f"Error: File not found - {rel_path}\n\n"
                        print(f"  Error: {error_msg.strip()}")
                        out_file.write(error_msg)
                    except PermissionError:
                        error_msg = f"Error: Permission denied reading file - {rel_path}\n\n"
                        print(f"  Error: {error_msg.strip()}")
                        out_file.write(error_msg)
                    except UnicodeDecodeError:
                        error_msg = f"Error: Could not read file (binary file) - {rel_path}\n\n"
                        print(f"  Error: {error_msg.strip()}")
                        out_file.write(error_msg)
                    except Exception as e:
                        error_msg = f"Error reading file - {rel_path}: {str(e)}\n\n"
                        print(f"  Error: {error_msg.strip()}")
                        out_file.write(error_msg)
            
            print("\nMarkdown generation completed successfully")
            return True, "Markdown file generated successfully!"
        except Exception as e:
            error_msg = f"Failed to generate markdown: {str(e)}"
            print(f"\nError during markdown generation: {error_msg}")
            return False, error_msg

    def generate_directory_tree(self, root_dir, exclude_patterns=None):
        """
        Generate a text representation of the directory structure.
        
        Args:
            root_dir (str): Root directory to start from
            exclude_patterns (set, optional): Patterns to exclude
            
        Returns:
            str: Markdown-formatted directory tree
        """
        print(f"Generating tree for directory: {root_dir}")
        
        # Store the tree structure
        tree_lines = []
        tree_lines.append("# Repository Structure\n")
        tree_lines.append("```")
        
        # Get the root directory name
        root_name = os.path.basename(root_dir) or os.path.basename(os.path.dirname(root_dir)) or root_dir
        tree_lines.append(f"📦 {root_name}")
        
        # Use a more robust tree generation approach
        def add_directory_to_tree(dir_path, prefix=""):
            entries = sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name.lower()))
            
            # Count entries to determine if an item is the last in its group
            total_entries = len(entries)
            
            for i, entry in enumerate(entries):
                is_last = (i == total_entries - 1)
                
                # Skip excluded items
                rel_path = os.path.relpath(entry.path, root_dir)
                if exclude_patterns and any(p in rel_path for p in exclude_patterns):
                    continue
                    
                # Choose the appropriate connector based on whether this is the last item
                connector = "└── " if is_last else "├── "
                
                # Add the entry to the tree
                if entry.is_dir():
                    tree_lines.append(f"{prefix}{connector}📂 {entry.name}")
                    
                    # For directories, recursively add their contents
                    # Use different prefix for children based on whether this is the last item
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    try:
                        add_directory_to_tree(entry.path, new_prefix)
                    except PermissionError:
                        tree_lines.append(f"{new_prefix}├── ⚠️ Permission denied")
                    except Exception as e:
                        tree_lines.append(f"{new_prefix}├── ⚠️ Error: {str(e)}")
                else:
                    tree_lines.append(f"{prefix}{connector}{entry.name}")
        
        try:
            # Start the recursive tree generation
            add_directory_to_tree(root_dir)
        except Exception as e:
            print(f"Error generating directory tree: {e}")
            tree_lines.append(f"⚠️ Error generating complete tree: {str(e)}")
        
        tree_lines.append("```\n")
        return '\n'.join(tree_lines)

    def generate_markdown_to_string(self, file_paths):
        """
        Generate markdown content as a string instead of writing to a file.
        
        Args:
            file_paths (list): List of file paths to combine
            
        Returns:
            tuple: (success, content_or_error_message)
        """
        print("\n=== Generating Markdown Content for Clipboard ===")
        print(f"Number of files to process: {len(file_paths)}")
        
        try:
            # Find the common root directory for all files
            if len(file_paths) > 0:
                # Get the directory that was originally selected
                common_prefix = os.path.commonpath([os.path.dirname(p) for p in file_paths])
                
                # Find the repository root
                repo_root = common_prefix
                while repo_root and not os.path.exists(os.path.join(repo_root, '.git')):
                    parent = os.path.dirname(repo_root)
                    if parent == repo_root:
                        break
                    repo_root = parent
                    
                if not os.path.exists(os.path.join(repo_root, '.git')):
                    repo_root = common_prefix
            else:
                common_prefix = ""
                repo_root = ""
                
            # Get exclude patterns
            exclude_patterns = getattr(self, 'exclude_patterns', None)
            
            # Use a string buffer instead of a file
            import io
            buffer = io.StringIO()
            
            # Generate and write directory tree at the beginning
            if repo_root:
                print("Generating directory tree...")
                tree_content = self.generate_directory_tree(repo_root, exclude_patterns)
                buffer.write(tree_content)
                buffer.write("\n\n# Selected Files\n\n")
                
            # Process each file
            for file_path in file_paths:
                if os.path.isdir(file_path):
                    continue
                    
                # Get relative path from common prefix
                rel_path = os.path.relpath(file_path, common_prefix)
                language = self.get_language_identifier(file_path)

                # Write file header with relative path
                buffer.write(f"# {rel_path}\n\n")

                # Read and write file contents
                try:
                    with open(file_path, 'r', encoding='utf-8') as in_file:
                        content = in_file.read()
                        buffer.write(f"```{language}\n{content}\n```\n\n")
                except Exception as e:
                    buffer.write(f"Error reading file - {rel_path}: {str(e)}\n\n")
            
            # Get the complete markdown content
            markdown_content = buffer.getvalue()
            buffer.close()
            
            return True, markdown_content
            
        except Exception as e:
            error_msg = f"Failed to generate markdown: {str(e)}"
            print(f"\nError during markdown generation: {error_msg}")
            return False, error_msg