import os

# Get the path to the DatabaseOperations folder
folder_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "DatabaseOperations")
)

# Loop through all the files in the folder
for filename in os.listdir(folder_path):
    # Check if the file is a Python file
    if filename.endswith(".py"):
        # Run the Python file using the system command
        os.system(f"python {os.path.join(folder_path, filename)}")
