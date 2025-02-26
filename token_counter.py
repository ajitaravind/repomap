import tiktoken
import mimetypes

class TokenCounter:
    # Binary file extensions that should be skipped
    BINARY_EXTENSIONS = {
        '.woff', '.woff2', '.ttf', '.eot', '.otf',  # Font files
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp',  # Images
        '.pdf', '.doc', '.docx',  # Documents
        '.zip', '.rar', '.7z', '.tar', '.gz',  # Archives
        '.exe', '.dll', '.so', '.dylib',  # Executables
        '.pyc', '.pyo',  # Python bytecode
    }

    def __init__(self):
        # Initialize with GPT-3.5-turbo encoding
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def is_binary_file(self, filepath):
        """
        Check if a file is binary based on its extension or content.
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            bool: True if the file is binary, False otherwise
        """
        # Check extension first
        ext = mimetypes.guess_extension(mimetypes.guess_type(filepath)[0] or '') or ''
        if ext.lower() in self.BINARY_EXTENSIONS:
            return True

        # If extension check doesn't conclusively identify it as binary,
        # try to read the first few bytes
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
                return bool(chunk.translate(None, textchars))
        except Exception:
            # If we can't read the file, assume it's binary to be safe
            return True
    
    def count_tokens(self, text):
        """
        Count tokens in the given text.
        
        Args:
            text (str): Text to count tokens in
            
        Returns:
            int: Number of tokens
        """
        return len(self.encoding.encode(text))
    
    def count_tokens_in_file(self, filepath):
        """
        Count tokens in a file.
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            int: Number of tokens in the file, or 0 for binary files
        """
        # Skip binary files
        if self.is_binary_file(filepath):
            return 0
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                return self.count_tokens(content)
        except Exception as e:
            raise IOError(f"Failed to count tokens in file '{filepath}': {str(e)}")
