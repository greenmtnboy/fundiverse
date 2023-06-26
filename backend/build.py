import subprocess
import sys
from pathlib import Path
import shutil
import os

# Path to the Python virtual environment
root = Path(__file__).parent

base = root.parent

virtual_env_path = f"{base}/.venv"


if __name__ == "__main__":
    print(f"{virtual_env_path}/scripts/python")
    # Command to execute
    command = [
        f"{virtual_env_path}/scripts/pyinstaller",
        "main.py",
        "--noconsole",
        "--onefile",
        "--name",
        "py-portfolio-ui-backend",
        "--hidden-import",
        "py-portfolio-index",
        "--collect-all",
        "py_portfolio_index",
        "--hidden-import",
        "alpaca-py",
        "--collect-all",
        "uvicorn",
        "--noconfirm",
        "--clean",
        "--additional-hooks-dir",
        "extra-hooks"
    ]

    try:
        # Execute the command
        subprocess.check_call(command, cwd=root)
    except subprocess.CalledProcessError as e:
        print("Error executing pyinstaller command:", e)
        sys.exit(1)

    # Move the executable to the root directory
        # Create the destination folder if it doesn't exist
    destination_folder = base / 'frontend' / 'src' / 'background'
    os.makedirs(destination_folder, exist_ok=True)
    pyinstaller_output_file = root / "dist" / "py-portfolio-ui-backend.exe"
    # Copy the PyInstaller output file to the destination folder
    print('copying to final location')
    shutil.copy(pyinstaller_output_file, destination_folder)
    print('file copied')
