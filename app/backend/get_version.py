import os
import re

def get_version():
    """
    Reads the version string from the project's __init__.py file.
    """
    # Get the absolute path to the directory containing this script (backend/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the __init__.py file (app/__init__.py)
    version_file_path = os.path.join(script_dir, '..', '__init__.py')

    try:
        with open(version_file_path, 'r') as f:
            version_file_content = f.read()
            # Use a regular expression to find the version string
            version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file_content, re.M)
            if version_match:
                return version_match.group(1)
            raise RuntimeError("Version string not found.")
    except FileNotFoundError:
        raise RuntimeError(f"Version file not found at {version_file_path}")

if __name__ == "__main__":
    version = get_version()
    print(version)
