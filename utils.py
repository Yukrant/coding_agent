import os
import shutil

def write_file(path, content):
    """Create a file with the given content at the specified path."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {path}: {str(e)}")
        return False

def read_file(path):
    """Read and return the contents of a file."""
    try:
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {path}: {str(e)}")
        return None

def copy_file(src, dst):
    """Copy a file from src to dst."""
    try:
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"Error copying file from {src} to {dst}: {str(e)}")
        return False

def ensure_dir(directory):
    """Make sure a directory exists."""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory}: {str(e)}")
        return False
