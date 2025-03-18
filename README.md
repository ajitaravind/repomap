# Markdown File Combiner

A simple Python-based GUI application for Windows that allows users to select and combine multiple program files from their local machine into a single markdown file. This markdown file can then be used to create a structured context for LLM input, while preserving file hierarchy and relationships. The application comes with built-in token counting and file filtering capabilities.

## Features

### File System Navigation

- Browse and select directories easily

### Smart File Filtering

- Filter files by extensions
- Exclude specific patterns/directories
- Auto-detect binary files

### Token Counting

- Real-time token counting for files
- Total token count for selected files
- Threading support for performance

### File Selection

- Checkbox-based file selection
- Recursive folder selection
- Visual indicators for different file types

## Installation

1. Clone the repository:
   - git clone https://github.com/ajitaravind/repomap.git
   - cd repomap

2. Create and activate a virtual environment:
   Windows:
   python -m venv venv
   venv\Scripts\activate

3. Install required packages:
   pip install tiktoken

## Usage

Run the application:

python main.py

Using the Interface:

1. Click "Browse" to select a directory
2. Use filters to include/exclude specific files
3. Check boxes next to files you want to include
4. Click "Copy to Clipboard" to generate the markdown and copy it to your clipboard

## Features in Detail

### File Filtering

- Enable/disable extension filtering
- Default extensions: `.py`, `.js`, `.md`
- Customizable exclude patterns
- Binary file detection

### Token Counting

- Real-time token calculation
- Background processing
- Progress indicators
- Cancellable operations

### File Selection

- Checkbox-based selection
- Folder-level selection
- Visual indicators:
  - ☐ Unchecked
  - ☑ Checked
  - ⊘ Excluded
  - ⚠ Error/Warning

### Visual Indicators

- Excluded directories: ⊘
- Symlinks: ↪
- Binary files: Yellow highlight
- Errors: Red highlight

## Error Handling

The application includes comprehensive error handling for:

- File permission issues
- Binary file detection
- Circular symlinks
- Invalid file encodings
- Threading errors

## Customization

You can customize:

- Color schemes in `main.py`
- Default excluded patterns in `file_handler.py`
- File extensions in `markdown_generator.py`
- Token counting settings in `token_counter.py`
- Platform-specific settings (currently tested on Windows, requires tweaks for Mac and Linux)

## License

This project is licensed under the MIT License
