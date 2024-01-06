import importlib
import subprocess

def install_module(module_name):
  try:
    importlib.import_module(module_name)
  except ImportError:
    try:
      subprocess.run(["pip", "install", module_name], check=True)
    except subprocess.CalledProcessError:
      raise ImportError(f"Failed to install module: {module_name}")

def execute_code_and_install_dependencies(code):
  try:
    # Create a dictionary to use as the local and global namespace for execution
    exec_namespace = {}
    # Extract import statements from the code
    import_statements = [line for line in code.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]
    # Extract module names from import statements
    module_names = [statement.split()[1] for statement in import_statements]
    # Install any missing modules
    for module_name in module_names:
      install_module(module_name)
    # Execute the code within the specified namespace
    exec(code, exec_namespace)
    # Check if the code defines a function named 'main' and execute it if present
    if 'main' in exec_namespace and callable(exec_namespace['main']):
      output = exec_namespace['main']()
      return output
    else:
      return "Code executed successfully."
  except ImportError as e:
    return f"Error: {e}"

# Example usage:
code_to_execute = """
import requests
from cryptography.fernet import Fernet

def main():
  response = requests.get("https://www.example.com")
  key = Fernet.generate_key()
  cipher_suite = Fernet(key)
  encrypted_text = cipher_suite.encrypt(b"Hello, world!")
  return response.text, encrypted_text
"""

result = execute_code_and_install_dependencies(code_to_execute)
print(result)
