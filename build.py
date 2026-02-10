import PyInstaller.__main__
import customtkinter  # type: ignore[import-untyped]
import os
import platform

# 1. Locate CustomTkinter library path
# We need to include its assets (json/images) explicitly in the executable
ctk_path = os.path.dirname(customtkinter.__file__)

# 2. Determine the path separator based on OS
# Windows uses ';', Mac/Linux uses ':'
separator = ';' if platform.system() == "Windows" else ':'

# 3. Define PyInstaller arguments
args = [
    'main.py',                  # Main script
    '--name=Buildeck',          # Name of the executable
    '--onefile',                # Bundle everything into a single file
    '--windowed',               # Hide the console window (GUI mode)
    '--clean',                  # Clean PyInstaller cache
    '--noconfirm',              # Do not ask for confirmation to overwrite
    
    # Include CustomTkinter assets
    f'--add-data={ctk_path}{separator}customtkinter',
    
    # Include our local assets (Locales, Icons if any)
    f'--add-data=assets{separator}assets',
    
    # (Optional) Add an icon if you have one. Uncomment next line:
    # '--icon=assets/icon.ico', 
]

print(f"Building executable for {platform.system()}...")
print(f"Including CustomTkinter from: {ctk_path}")

# 4. Run PyInstaller
PyInstaller.__main__.run(args)