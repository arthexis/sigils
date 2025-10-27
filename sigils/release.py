import os
import subprocess
import toml


def update_patch_version(pyproject_path, debug=False):
    """Updates the patch version in pyproject.toml."""
    with open(pyproject_path, 'r') as f:
        config = toml.load(f)
    
    version = config["project"]["version"].split('.')
    version[-1] = str(int(version[-1]) + 1)
    config["project"]["version"] = '.'.join(version)
    
    with open(pyproject_path, 'w') as f:
        toml.dump(config, f)
    
    if debug:
        print(f"Updated version to: {config['project']['version']}")
    
    return config["project"]["version"]


def build_and_upload(debug=False):
    """Builds the package and uploads it to PyPI."""
    if debug:
        print("Building package...")
    subprocess.run(["python", "-m", "build"])
    
    if debug:
        print("Uploading package...")
    subprocess.run(["twine", "upload", "dist/*"], env=os.environ)
