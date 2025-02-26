import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import ctypes
import threading
import queue
from file_handler import FileHandler
from token_counter import TokenCounter
from markdown_generator import MarkdownGenerator

class MainApplication:
    def __init__(self, root):
        # Enable DPI awareness for better text rendering
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass  # Fallback for older Windows versions

        self.root = root
        self.root.title("Markdown File Combiner")
        self.root.geometry("1000x700")

        # Configure modern styles
        self.setup_styles()

        self.file_handler = FileHandler()
        self.token_counter = TokenCounter()
        self.markdown_generator = MarkdownGenerator()
        
        # Track which directories have been calculated
        self.calculated_directories = set()
        
        # Threading support
        self.token_queue = queue.Queue()
        self.cancel_operation = False
        self.active_threads = set()
        
        self.setup_ui()

    def setup_styles(self):
        """Configure custom styles for the application"""
        style = ttk.Style()
        
        # Configure colors with better contrast
        self.colors = {
            'primary': '#0078D4',      # Windows blue
            'secondary': '#E5E5E5',    # Light gray
            'accent': '#60CDFF',       # Light blue
            'success': '#28A745',      # Green
            'warning': '#FFC107',      # Yellow
            'error': '#DC3545',        # Red
            'text': '#000000',         # Pure black for better contrast
            'text_secondary': '#505050',# Darker gray for better readability
            'background': '#FFFFFF'     # Pure white background
        }

        # Configure common styles
        style.configure('Main.TFrame', background=self.colors['background'])
        style.configure('Header.TFrame', background=self.colors['primary'])
        
        # Button styles - using native button look with custom colors
        style.configure('Primary.TButton',
            padding=(10, 5),
            font=('Segoe UI Semibold', 11))  # Increased from 9
        
        # Entry styles with better contrast
        style.configure('Main.TEntry',
            fieldbackground='white',
            font=('Segoe UI', 11),  # Increased from 9
            padding=5)
            
        # Label styles with improved readability
        style.configure('Header.TLabel',
            background=self.colors['primary'],
            foreground='white',
            font=('Segoe UI Semibold', 13))  # Increased from 11
        style.configure('Main.TLabel',
            background=self.colors['background'],
            foreground=self.colors['text'],
            font=('Segoe UI', 11))  # Increased from 9
            
        # Labelframe styles with better definition
        style.configure('Card.TLabelframe',
            background=self.colors['background'])
        style.configure('Card.TLabelframe.Label',
            background=self.colors['background'],
            foreground=self.colors['text'],
            font=('Segoe UI Semibold', 11))  # Increased from 9
            
        # Treeview styles with improved clarity
        style.configure('Main.Treeview',
            background='white',
            foreground=self.colors['text'],
            rowheight=28,  # Increased from 24 to accommodate larger font
            fieldbackground='white',
            font=('Segoe UI', 11))  # Increased from 9
        style.configure('Main.Treeview.Heading',
            background=self.colors['secondary'],
            foreground=self.colors['text'],
            font=('Segoe UI Semibold', 11))  # Increased from 9
        style.map('Main.Treeview',
            background=[('selected', self.colors['primary'])],
            foreground=[('selected', 'white')])
            
        # Checkbutton styles
        style.configure('TCheckbutton',
            background=self.colors['background'],
            foreground=self.colors['text'],
            font=('Segoe UI', 11))  # Increased from 9

    def setup_ui(self):
        # Configure root window with white background
        self.root.configure(bg=self.colors['background'])
        
        # Add padding to the entire window
        main_container = ttk.Frame(self.root, style='Main.TFrame', padding="10")  # Increased padding
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header frame with stronger visual presence
        header_frame = ttk.Frame(main_container, style='Header.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Directory selection in header with improved spacing
        ttk.Label(header_frame, 
                 text="Select Directory", 
                 style='Header.TLabel').pack(side=tk.LEFT, padx=10, pady=10)
        self.dir_entry = ttk.Entry(header_frame, width=60, style='Main.TEntry')  # Increased width
        self.dir_entry.pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(header_frame, 
                  text="Browse", 
                  style='Primary.TButton',
                  command=self.browse_directory).pack(side=tk.LEFT, padx=5, pady=10)
        
        self.expand_button = ttk.Button(header_frame,
                  text="Expand All",
                  style='Primary.TButton',
                  command=self.expand_all_folders)
        self.expand_button.pack(side=tk.LEFT, padx=5, pady=10)
        self.expand_button.configure(state='disabled')  # Disabled by default
        
        self.collapse_button = ttk.Button(header_frame,
                  text="Collapse All",
                  style='Primary.TButton',
                  command=self.collapse_all_folders)
        self.collapse_button.pack(side=tk.LEFT, padx=5, pady=10)
        self.collapse_button.configure(state='disabled')  # Disabled by default

        # Main content frame with consistent spacing
        main_frame = ttk.Frame(main_container, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        # Filter frame
        self.create_filter_frame(main_frame)

        # Files frame with improved visual hierarchy
        files_frame = ttk.LabelFrame(main_frame, 
                                   text="Files", 
                                   style='Card.TLabelframe',
                                   padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create treeview with sharper text
        self.tree = ttk.Treeview(files_frame, 
                                columns=("Tokens",), 
                                selectmode="browse",
                                style='Main.Treeview')
        
        # Configure treeview tags with better contrast
        self.tree.tag_configure('excluded', foreground=self.colors['text_secondary'])
        self.tree.tag_configure('binary', foreground=self.colors['warning'])
        self.tree.tag_configure('error', foreground=self.colors['error'])

        self.tree.heading("#0", text="Files", anchor=tk.W)
        self.tree.heading("Tokens", text="Tokens", anchor=tk.W)
        self.tree.column("#0", width=600, anchor=tk.W)  # Increased width
        self.tree.column("Tokens", width=150, anchor=tk.W)  # Increased width

        # Add scrollbar
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom frame with consistent styling
        bottom_frame = ttk.Frame(main_container, style='Main.TFrame', padding="10")
        bottom_frame.pack(fill=tk.X, pady=(5, 0))

        self.total_tokens_label = ttk.Label(bottom_frame, 
                                          text="Total Tokens: 0",
                                          style='Main.TLabel')
        self.total_tokens_label.pack(side=tk.LEFT)

        self.status_frame = ttk.Frame(bottom_frame, style='Main.TFrame')
        self.status_frame.pack(side=tk.RIGHT, padx=5)
        
        self.progress_bar = ttk.Progressbar(self.status_frame, 
                                          mode='indeterminate', 
                                          length=200)
        
        self.status_label = ttk.Label(self.status_frame,
                                    text="",
                                    style='Main.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(self.status_frame,
                                      text="Cancel",
                                      style='Primary.TButton',
                                      command=self.cancel_current_operation,
                                      state='disabled')
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(bottom_frame, 
                  text="Copy to Clipboard",
                  style='Primary.TButton',
                  command=self.copy_markdown_to_clipboard).pack(side=tk.RIGHT, padx=5)

        # Bind events
        self.tree.bind('<Button-1>', self.handle_click)
        self.tree.bind('<<TreeviewOpen>>', lambda e: self.on_folder_open())
        self.tree.bind('<<TreeviewClose>>', lambda e: self.on_folder_close())

        # Store checked items
        self.checked_items = set()

    def create_filter_frame(self, parent):
        filter_frame = ttk.LabelFrame(parent, 
                                    text="Filters", 
                                    style='Card.TLabelframe',
                                    padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # File Extensions Filter
        ext_frame = ttk.LabelFrame(filter_frame, 
                                 text="File Extensions", 
                                 style='Card.TLabelframe',
                                 padding="10")
        ext_frame.pack(fill=tk.X, pady=(0, 8))

        self.filter_entry = ttk.Entry(ext_frame, width=40, style='Main.TEntry')  
        self.filter_entry.pack(side=tk.LEFT, padx=8, pady=5)  
        self.filter_entry.configure(state='disabled')
        self.filter_entry.insert(0, ".py,.js,.md")

        self.filter_button = ttk.Button(ext_frame, 
                                      text="Apply Filter",
                                      style='Primary.TButton',
                                      command=self.refresh_files)
        self.filter_button.pack(side=tk.LEFT, padx=8, pady=5)  
        self.filter_button.configure(state='disabled')

        self.filter_enabled = tk.BooleanVar(value=False)
        self.filter_checkbox = ttk.Checkbutton(ext_frame,
                                             text="Enable Filtering",
                                             variable=self.filter_enabled,
                                             command=self.toggle_filter)
        self.filter_checkbox.pack(side=tk.LEFT, padx=8, pady=5)  

        # Excluded Patterns Filter
        exclude_frame = ttk.LabelFrame(filter_frame,
                                     text="Excluded Patterns",
                                     style='Card.TLabelframe',
                                     padding="10")
        exclude_frame.pack(fill=tk.X)

        default_excludes = ','.join(sorted(self.file_handler.DEFAULT_EXCLUDE_PATTERNS))
        
        self.exclude_entry = ttk.Entry(exclude_frame, width=70, style='Main.TEntry')  
        self.exclude_entry.pack(side=tk.LEFT, padx=8, pady=5)  
        self.exclude_entry.insert(0, default_excludes)
        self.exclude_entry.configure(state='normal')

        self.exclude_enabled = tk.BooleanVar(value=True)
        self.exclude_checkbox = ttk.Checkbutton(exclude_frame,
                                              text="Enable Exclusions",
                                              variable=self.exclude_enabled,
                                              command=self.toggle_exclude)
        self.exclude_checkbox.pack(side=tk.LEFT, padx=8, pady=5)  

    def toggle_filter(self):
        """Enable or disable the filter controls based on checkbox state"""
        if self.filter_enabled.get():
            self.filter_entry.configure(state='normal')
            self.filter_button.configure(state='normal')
        else:
            self.filter_entry.configure(state='disabled')
            self.filter_entry.delete(0, tk.END)
            self.filter_entry.insert(0, ".py,.js,.md")
            self.refresh_files()

    def toggle_exclude(self):
        """Enable or disable the exclude patterns based on checkbox state"""
        if self.exclude_enabled.get():
            self.exclude_entry.configure(state='normal')
            # Update file handler with current patterns
            patterns = {p.strip() for p in self.exclude_entry.get().split(',') if p.strip()}
            self.file_handler = FileHandler(exclude_patterns=patterns)
        else:
            self.exclude_entry.configure(state='disabled')
            # Clear exclusions
            self.file_handler = FileHandler(exclude_patterns=set())
        
        self.refresh_files()

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.refresh_files()

    def refresh_files(self):
        directory = self.dir_entry.get()
        if not directory:
            self.expand_button.configure(state='disabled')
            self.collapse_button.configure(state='disabled')
            return

        # Enable buttons since we have a directory
        self.expand_button.configure(state='normal')
        self.collapse_button.configure(state='normal')

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear checked items
        self.checked_items.clear()
        
        # Clear visited paths in file handler to prevent false circular reference detection
        self.file_handler.clear_visited_paths()

        # Get extensions filter
        extensions = [ext.strip() for ext in self.filter_entry.get().split(",")]

        try:
            # Add root directory
            self.populate_tree("", directory, extensions)

        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.update_total_tokens()

    def calculate_directory_tokens(self, directory_path):
        """Calculate tokens for all markdown files in a directory"""
        if directory_path in self.calculated_directories:
            return
        
        self.calculate_tokens_for_directory(directory_path)
    
    def clear_token_calculations(self):
        """Clear all token calculations and reset the UI"""
        self.calculated_directories.clear()
        self.cancel_operation = True
        
        # Clear token counts from tree
        for item_id in self.tree.get_children():
            values = list(self.tree.item(item_id)['values'])
            if len(values) > 1:
                values[1] = ""
                self.tree.item(item_id, values=values)
        
        # Reset total tokens display
        self.total_tokens_label.config(text="Total Tokens: 0")
        
        # Clean up any ongoing calculations
        self.cleanup_calculation_ui()

    def calculate_tokens_for_directory(self, directory_path):
        """Calculate tokens for a directory in a separate thread"""
        self.status_label.config(text=f"Calculating tokens for {os.path.basename(directory_path)}...")
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        self.progress_bar.start(10)
        self.cancel_button.config(state='normal')
        
        def token_calculation_thread():
            try:
                total_tokens = 0
                
                # Get all files in the directory
                for root, _, filenames in os.walk(directory_path):
                    if self.cancel_operation:
                        self.token_queue.put(("cancelled", None))
                        return
                        
                    for filename in filenames:
                        if self.cancel_operation:
                            self.token_queue.put(("cancelled", None))
                            return
                            
                        item_path = os.path.join(root, filename)
                        
                        # Skip binary files and excluded files
                        try:
                            if self.token_counter.is_binary_file(item_path):
                                continue
                                
                            rel_path = os.path.relpath(item_path, self.dir_entry.get())
                            if self.exclude_enabled.get() and self.file_handler.should_exclude(rel_path):
                                continue
                                
                            # Only count files that match the filter
                            extensions = [ext.strip() for ext in self.filter_entry.get().split(",")]
                            if extensions and not any(item_path.lower().endswith(ext.lower()) for ext in extensions):
                                continue
                                
                            # Count tokens
                            try:
                                tokens = self.token_counter.count_tokens_in_file(item_path)
                                total_tokens += tokens
                                self.token_queue.put(("progress", (item_path, tokens)))
                            except Exception as e:
                                self.token_queue.put(("error", (item_path, str(e))))
                        except Exception as e:
                            self.token_queue.put(("error", (item_path, str(e))))
                
                self.token_queue.put(("done", (directory_path, total_tokens)))
            except Exception as e:
                self.token_queue.put(("error", (directory_path, str(e))))
            finally:
                self.active_threads.discard(thread)
        
        thread = threading.Thread(target=token_calculation_thread)
        self.active_threads.add(thread)
        thread.start()
        
        # Schedule the check_token_queue method
        self.root.after(100, self.check_token_queue)
        
        return thread
        
    def check_token_queue(self):
        """Check the token queue for updates from token calculations"""
        try:
            while True:
                try:
                    status, data = self.token_queue.get_nowait()
                    
                    if status == "progress":
                        item_path, tokens = data
                        self.update_item_tokens(item_path, tokens)
                    elif status == "error":
                        path, error_msg = data
                        self.show_error(f"Error processing {path}: {error_msg}")
                        if hasattr(self, 'pending_calculations') and self.pending_calculations > 0:
                            self.pending_calculations -= 1
                    elif status == "done":
                        directory_path, total_tokens = data
                        self.calculated_directories.add(directory_path)
                        
                        if hasattr(self, 'pending_calculations'):
                            if hasattr(self, 'calculation_results'):
                                self.calculation_results[directory_path] = total_tokens
                        
                            if self.pending_calculations > 0:
                                self.pending_calculations -= 1
                                print(f"Completed calculation for {directory_path}. Pending: {self.pending_calculations}")
                            
                            # Update UI if all calculations are complete
                            if self.pending_calculations <= 0:
                                if hasattr(self, 'calculation_results'):
                                    total = sum(self.calculation_results.values())
                                    print(f"All calculations complete. Total tokens: {total}")
                                    self.update_total_tokens(total)
                                self.cleanup_calculation_ui()
                                self.status_label.config(text="All token calculations complete")
                        else:
                            # Legacy behavior
                            self.update_total_tokens(total_tokens)
                            self.cleanup_calculation_ui()
                    elif status == "cancelled":
                        self.show_info("Token calculation cancelled")
                        if hasattr(self, 'pending_calculations'):
                            self.pending_calculations = 0
                        self.cleanup_calculation_ui()
                
                except queue.Empty:
                    if not any(t.is_alive() for t in self.active_threads):
                        if hasattr(self, 'pending_calculations') and self.pending_calculations > 0:
                            self.show_error("Some token calculations failed to complete")
                        self.cleanup_calculation_ui()
                    else:
                        # Schedule next check
                        self.root.after(100, self.check_token_queue)
                    break
        except Exception as e:
            self.show_error(f"Error checking token queue: {str(e)}")
            self.cleanup_calculation_ui()

    def cleanup_calculation_ui(self):
        """Clean up UI elements after calculation is complete"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.cancel_button.config(state='disabled')
        self.status_label.config(text="")
        self.cancel_operation = False
    
    def update_item_tokens(self, item_path, tokens):
        """Update token count for a specific item"""
        for item_id in self.tree.get_children():
            if self.tree.item(item_id)['values'][0] == item_path:
                values = list(self.tree.item(item_id)['values'])
                values[1] = tokens
                self.tree.item(item_id, values=values)
                break
    
    def update_total_tokens(self, total_tokens=None):
        """Update the total token count display.
        
        Args:
            total_tokens (int, optional): If provided, updates the label with this value.
                                        If None, recalculates the total from checked items.
        """
        if total_tokens is None:
            total_tokens = 0
            # Create a copy of checked_items to avoid modification during iteration
            items_to_remove = set()
            
            # First, collect all individual files that are checked
            checked_files = set()
            for item in self.checked_items:
                try:
                    # Check if the item still exists in the tree
                    tree_item = self.tree.item(item)
                    tags = tree_item['tags']
                    
                    # Skip excluded items
                    if 'excluded' in tags:
                        continue
                    
                    # If it's a file, add it to our checked files
                    if 'file' in tags and item not in checked_files:
                        checked_files.add(item)
                    
                except Exception as e:
                    print(f"Error processing item {item} for token count: {e}")
                    # If the item doesn't exist anymore, mark it for removal
                    items_to_remove.add(item)
            
            # Now calculate the total tokens from all checked files
            for file_path in checked_files:
                try:
                    tree_item = self.tree.item(file_path)
                    values = tree_item['values']
                    
                    if values and len(values) > 0:
                        # Skip binary files and error files in token count
                        if values[0] not in ("(binary)", "(error)", "(excluded)", "(symlink)", "(skipped)"):
                            try:
                                # Make sure we have a valid token count
                                if values[0] and str(values[0]).isdigit():
                                    total_tokens += int(values[0])
                            except (ValueError, TypeError):
                                # Skip if token count is not a valid number
                                pass
                except Exception as e:
                    print(f"Error processing file {file_path} for token count: {e}")
            
            # Remove any non-existent items from checked_items
            self.checked_items.difference_update(items_to_remove)
        
        # Update the label with the total token count
        print(f"Updating total token count to: {total_tokens}")
        self.total_tokens_label.config(text=f"Total Tokens: {total_tokens}")

    def get_files_from_folder(self, folder_path):
        """Recursively get all files from a folder."""
        files = []
        try:
            for root, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    # Skip binary files
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            f.read(1024)  # Try to read first 1KB
                        files.append(file_path)
                    except (UnicodeDecodeError, PermissionError):
                        print(f"  Skipping binary/unreadable file: {file_path}")
                        continue
        except Exception as e:
            print(f"Error accessing folder {folder_path}: {e}")
        return files

    def copy_markdown_to_clipboard(self):
        """Generate markdown content and copy it to clipboard instead of saving to file"""
        print("\n=== Starting Markdown Generation for Clipboard ===")
        if not self.checked_items:
            print("No items checked in the tree")
            messagebox.showwarning("Warning", "No files selected!")
            return

        print(f"Total checked items: {len(self.checked_items)}")
        
        selected_files = []
        for item in self.checked_items:
            try:
                # Get item details
                tree_item = self.tree.item(item)
                values = tree_item['values']
                tags = tree_item['tags']
                
                if 'folder' in tags:
                    folder_files = self.get_files_from_folder(item)
                    selected_files.extend(folder_files)
                    continue
                    
                # Skip binary and error files
                if values and values[0] in ("(binary)", "(error)"):
                    continue
                    
                # Add valid file to the list
                selected_files.append(item)
                
            except Exception as e:
                print(f"Error processing item {item}: {e}")

        # Remove duplicates while preserving order
        selected_files = list(dict.fromkeys(selected_files))
        
        print(f"\nTotal files selected for markdown: {len(selected_files)}")

        if not selected_files:
            print("No valid text files found to process")
            messagebox.showwarning("Warning", "No valid text files selected!")
            return

        # Pass exclude patterns to markdown generator
        if self.exclude_enabled.get():
            exclude_patterns = {p.strip() for p in self.exclude_entry.get().split(',') if p.strip()}
            self.markdown_generator.exclude_patterns = exclude_patterns
        else:
            self.markdown_generator.exclude_patterns = set()
        
        # Generate markdown content to memory instead of file
        success, content_or_error = self.markdown_generator.generate_markdown_to_string(selected_files)
        
        if success:
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(content_or_error)
            messagebox.showinfo("Success", "Markdown copied to clipboard!")
        else:
            messagebox.showerror("Error", content_or_error)

    def cancel_current_operation(self):
        self.cancel_operation = True

    def show_error(self, message):
        """Show error message in a dialog"""
        messagebox.showerror("Error", message)
    
    def show_info(self, message):
        """Show info message in a dialog"""
        messagebox.showinfo("Info", message)

    def populate_tree(self, parent, path, extensions):
        try:
            # Normalize path separators
            path = os.path.normpath(path)
            
            # Check if path is safe (no symlink cycles)
            if not self.file_handler.is_safe_path(path):
                self.tree.insert(parent, tk.END, 
                               text="⚠ Skipped: Potential circular reference", 
                               values=("(skipped)",), 
                               tags=('error',))
                return
            
            # List directory contents
            items = os.listdir(path)

            # Add folders first
            for item in sorted(items):
                item_path = os.path.normpath(os.path.join(path, item))
                rel_path = os.path.relpath(item_path, self.dir_entry.get())
                
                try:
                    if os.path.islink(item_path):
                        # Show symlinks with a special indicator
                        target_path = os.path.realpath(item_path)
                        if os.path.isdir(item_path):
                            self.tree.insert(parent, tk.END, 
                                          iid=item_path, 
                                          text=f"↪ {item} → {target_path}", 
                                          values=("(symlink)",), 
                                          tags=('folder', 'symlink'))
                        continue
                        
                    if os.path.isdir(item_path):
                        folder_id = item_path
                        # Check if folder should be excluded
                        if self.exclude_enabled.get() and self.file_handler.should_exclude(rel_path):
                            folder = self.tree.insert(parent, tk.END, 
                                                    iid=folder_id, 
                                                    text=f"⊘ {item}", 
                                                    values=("(excluded)",), 
                                                    tags=('folder', 'excluded'))
                        else:
                            folder = self.tree.insert(parent, tk.END, 
                                                    iid=folder_id, 
                                                    text=f"☐ {item}", 
                                                    values=("",), 
                                                    tags=('folder',))
                        # Add a dummy child to show the folder indicator
                        self.tree.insert(folder, tk.END, text="", tags=('dummy',))

                except OSError as e:
                    # Handle permission errors or other OS-level issues
                    self.tree.insert(parent, tk.END, 
                                   text=f"⚠ {item}: {str(e)}", 
                                   values=("(error)",), 
                                   tags=('error',))
                    continue

            # Then add files
            for item in sorted(items):
                item_path = os.path.normpath(os.path.join(path, item))
                rel_path = os.path.relpath(item_path, self.dir_entry.get())
                if os.path.isfile(item_path):
                    try:
                        # Check if file should be excluded
                        if self.exclude_enabled.get() and self.file_handler.should_exclude(rel_path):
                            self.tree.insert(parent, tk.END, 
                                          iid=item_path, 
                                          text=f"⊘ {item}", 
                                          values=("(excluded)",), 
                                          tags=('file', 'excluded'))
                            continue

                        # Check if the file matches any of the extensions
                        if not extensions or any(item.lower().endswith(ext.lower()) for ext in extensions):
                            try:
                                # For binary files, token_count will be 0
                                token_count = self.token_counter.count_tokens_in_file(item_path)
                                if token_count == 0 and self.token_counter.is_binary_file(item_path):
                                    # Mark binary files with a special indicator
                                    self.tree.insert(parent, tk.END, 
                                                   iid=item_path, 
                                                   text=f"☐ {item}", 
                                                   values=("(binary)",), 
                                                   tags=('file', 'binary'))
                                else:
                                    self.tree.insert(parent, tk.END, 
                                                   iid=item_path, 
                                                   text=f"☐ {item}", 
                                                   values=(token_count,), 
                                                   tags=('file',))
                            except Exception as e:
                                # Still insert the file, but mark it as unreadable
                                self.tree.insert(parent, tk.END, 
                                               iid=item_path, 
                                               text=f"☐ {item}", 
                                               values=("(error)",), 
                                               tags=('file', 'error'))
                    except OSError as e:
                        # Handle permission errors
                        self.tree.insert(parent, tk.END, 
                                       text=f"⚠ {item}: {str(e)}", 
                                       values=("(error)",), 
                                       tags=('error',))

        except Exception as e:
            print(f"Error populating tree for path {path}: {e}")

    def on_folder_open(self):
        item = self.tree.focus()
        if item:
            children = self.tree.get_children(item)
            # Check if this folder only has a dummy node or no children
            if not children or (len(children) == 1 and 'dummy' in self.tree.item(children[0])['tags']):
                # Remove any existing dummy nodes
                for child in children:
                    if 'dummy' in self.tree.item(child)['tags']:
                        self.tree.delete(child)
                # Populate with real contents
                path = item
                extensions = [ext.strip() for ext in self.filter_entry.get().split(",")]
                self.populate_tree(item, path, extensions)

    def on_folder_close(self):
        # When closing a folder, deselect all its children
        item = self.tree.focus()
        if item:
            # Only deselect if the folder itself is not checked
            text = self.tree.item(item, "text")
            if not text.startswith("☑"):
                self.uncheck_item_and_children(item)
            self.update_total_tokens()

    def expand_all_folders(self):
        """Expand all folders in the tree view and select all items"""
        if not self.dir_entry.get():
            return
        
        # Clear any existing selections first
        self.checked_items.clear()
        
        # Reset calculation tracking
        self.pending_calculations = 0
        self.calculation_results = {}
        self.cancel_operation = False
        
        # Track folders that need token calculation
        folders_to_calculate = []
        
        def expand_and_select_children(item):
            # Get the item's tags to check if it's a folder
            tags = self.tree.item(item)['tags']
            
            # Skip excluded items
            if 'excluded' in tags:
                return
            
            # Check this item (select it)
            self.check_item_and_children(item, skip_calculation=True)
            
            if 'folder' in tags:
                # If it's a folder, expand it first
                self.tree.item(item, open=True)
                
                # Populate its contents if not already populated
                children = self.tree.get_children(item)
                if not children or (len(children) == 1 and 'dummy' in self.tree.item(children[0])['tags']):
                    # Remove any existing dummy nodes
                    for child in children:
                        if 'dummy' in self.tree.item(child)['tags']:
                            self.tree.delete(child)
                    # Populate with real contents
                    extensions = [ext.strip() for ext in self.filter_entry.get().split(",")]
                    self.populate_tree(item, item, extensions)
                
                # Add to folders that need calculation if not already calculated
                if item not in self.calculated_directories:
                    folders_to_calculate.append(item)
                
                # Recursively expand and select all children
                for child in self.tree.get_children(item):
                    expand_and_select_children(child)
        
        # Start expanding and selecting from root items
        for item in self.tree.get_children():
            expand_and_select_children(item)
        
        # Now calculate tokens for all folders that need it
        if folders_to_calculate:
            self.status_label.config(text=f"Calculating tokens for {len(folders_to_calculate)} folders...")
            self.progress_bar.pack(side=tk.LEFT, padx=5)
            self.progress_bar.start(10)
            self.cancel_button.config(state='normal')
            
            # Set the pending calculations count
            self.pending_calculations = len(folders_to_calculate)
            print(f"Starting calculation for {len(folders_to_calculate)} folders")
            
            # Process folders breadth-first (parent directories first)
            for folder in folders_to_calculate:
                if self.cancel_operation:
                    break
                self.calculate_tokens_for_directory(folder)
        else:
            # If no calculations needed, just update total tokens
            self.update_total_tokens()
        
        # Show a confirmation message
        self.show_info(f"All items expanded and selected ({len(self.checked_items)} items)")

    def collapse_all_folders(self):
        """Collapse all folders in the tree view and deselect all items"""
        if not self.dir_entry.get():
            return
        
        # Clear all selections first
        self.checked_items.clear()
        
        def collapse_and_deselect_folder_recursive(item):
            # Get the item's tags and text
            tags = self.tree.item(item)['tags']
            text = self.tree.item(item, "text")
            
            # Deselect this item (if not excluded)
            if 'excluded' not in tags and text.startswith("☑"):
                self.tree.item(item, text=f"☐ {text[2:]}")
            
            if 'folder' in tags:
                # First process all children recursively
                for child in self.tree.get_children(item):
                    collapse_and_deselect_folder_recursive(child)
                    
                # Then collapse this folder
                self.tree.item(item, open=False)
        
        # Start collapsing and deselecting from root items
        for item in self.tree.get_children():
            collapse_and_deselect_folder_recursive(item)
        
        # Update the total tokens count
        self.update_total_tokens()
        
        # Show a confirmation message
        self.show_info("All folders collapsed and items deselected")

    def handle_click(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if item:
            # Get the item's tags to check if it's a folder and if it's excluded
            tags = self.tree.item(item)['tags']
            
            # Don't process clicks on excluded items
            if 'excluded' in tags:
                return
            
            # Get the text to determine if we're clicking on a checkbox
            text = self.tree.item(item, "text")
            
            # Handle checkbox toggling
            if text.startswith("☐"):
                # Select this item and all its children recursively
                # This will also expand folders and populate their contents
                self.check_item_and_children(item, skip_calculation=True)
                
            elif text.startswith("☑"):
                # Deselect this item and all its children recursively
                self.uncheck_item_and_children(item)
        
            # If it's a folder and we're not clicking on the checkbox, just expand/collapse
            elif 'folder' in tags:
                # If it's a folder, populate its contents if not already populated
                children = self.tree.get_children(item)
                if not children or (len(children) == 1 and 'dummy' in self.tree.item(children[0])['tags']):
                    # Remove any existing dummy nodes
                    for child in children:
                        if 'dummy' in self.tree.item(child)['tags']:
                            self.tree.delete(child)
                    # Populate with real contents
                    extensions = [ext.strip() for ext in self.filter_entry.get().split(",")]
                    self.populate_tree(item, item, extensions)
            
                # Calculate directory tokens if not already calculated
                if item not in self.calculated_directories:
                    self.calculate_tokens_for_directory(item)
        
        self.update_total_tokens()

    def check_item_and_children(self, item, skip_calculation=False):
        """Recursively check an item and all its children
        
        Args:
            item: The tree item to check
            skip_calculation: If True, skip token calculation for folders
        """
        # Check if the item is excluded
        if 'excluded' in self.tree.item(item)['tags']:
            return
            
        # Check this item
        text = self.tree.item(item, "text")
        self.tree.item(item, text=f"☑ {text[2:]}")
        self.checked_items.add(item)
        
        # If it's a folder, make sure it's expanded
        tags = self.tree.item(item)['tags']
        if 'folder' in tags:
            # Expand the folder
            self.tree.item(item, open=True)
            
            # Populate its contents if not already populated
            children = self.tree.get_children(item)
            if not children or (len(children) == 1 and 'dummy' in self.tree.item(children[0])['tags']):
                # Remove any existing dummy nodes
                for child in children:
                    if 'dummy' in self.tree.item(child)['tags']:
                        self.tree.delete(child)
                # Populate with real contents
                extensions = [ext.strip() for ext in self.filter_entry.get().split(",")]
                self.populate_tree(item, item, extensions)
            
            # Calculate directory tokens if not already calculated and not skipping calculation
            if not skip_calculation and item not in self.calculated_directories:
                self.calculate_tokens_for_directory(item)
    
        # Check all children recursively
        for child in self.tree.get_children(item):
            self.check_item_and_children(child, skip_calculation)

    def uncheck_item_and_children(self, item):
        """Recursively uncheck an item and all its children"""
        # Check if the item is excluded
        if 'excluded' in self.tree.item(item)['tags']:
            return
            
        # Uncheck this item
        text = self.tree.item(item, "text")
        self.tree.item(item, text=f"☐ {text[2:]}")
        self.checked_items.discard(item)
        
        # Uncheck all children recursively
        for child in self.tree.get_children(item):
            self.uncheck_item_and_children(child)

def main():
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()

if __name__ == "__main__":
    main()