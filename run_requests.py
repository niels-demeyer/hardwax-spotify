import os
import subprocess

# Get the path to the requests folder
requests_folder = "requests"

# List all the .py files in the requests folder
py_files = [f for f in os.listdir(requests_folder) if f.endswith(".py")]

# Run each .py file using subprocess
for py_file in py_files:
    py_path = os.path.join(requests_folder, py_file)
    print(f"Running {py_file}...")
    subprocess.run(["python", py_path])

print()  # Add a newline character
