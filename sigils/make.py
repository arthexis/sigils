# make.py
import os
import shutil
import subprocess
from sigils import Sigil


def find_makefile_template(directory, debug=False):
    """Finds a makefile template in the given directory."""
    for filename in os.listdir(directory):
        if filename in ('%[.makefile]', '%[makefile]'):
            return os.path.join(directory, filename)
    return None


def process_makefile(directory, context, debug=False):
    """Processes the makefile template to create the actual makefile."""
    template_path = find_makefile_template(directory, debug)
    if not template_path:
        if debug:
            print("No makefile template found.")
        return None
    
    resolved_name = Sigil(template_path).solve(context)
    output_path = os.path.join(directory, resolved_name)
    
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    result = Sigil(template_content) % context
    
    with open(output_path, 'w') as f:
        f.write(result)
    
    if debug:
        print(f"Makefile generated: {output_path}")
    
    return output_path


def run_make(directory, target=None, debug=False):
    """Runs the make command in the given directory."""
    if not shutil.which("make"):
        print("Error: 'make' command not found.")
        return
    
    cmd = ["make"]
    if target:
        cmd.append(target)
    
    subprocess.run(cmd, cwd=directory)
