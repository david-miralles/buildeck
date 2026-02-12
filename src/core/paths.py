import sys
import os

def get_user_data_dir(app_name="Buildeck"):
    """
    Returns a secure and writable path for data storage based on the OS.
    - Windows: %APPDATA%/Buildeck
    - macOS: ~/Library/Application Support/Buildeck
    - Linux: ~/.local/share/Buildeck
    """
    if sys.platform == "win32":
        base_path = os.environ.get("APPDATA")
    elif sys.platform == "darwin":
        base_path = os.path.expanduser("~/Library/Application Support")
    else:
        # Linux and others
        base_path = os.path.expanduser("~/.local/share")
    
    full_path = os.path.join(base_path, app_name)
    
    # Ensure the directory exists to avoid IO errors
    os.makedirs(full_path, exist_ok=True)
    
    return full_path