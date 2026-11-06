import socket
s = socket.create_connection(("192.168.5.1", 29999), timeout=8)
s.settimeout(5)
def send(cmd):
    s.sendall((cmd + "\n").encode())
    try:
        return s.recv(400).decode("utf-8", "replace").strip()
    except Exception as e:
        return "ERR:" + str(e)
print("ClearError ->", send("ClearError()"))
print("RobotMode ->", send("RobotMode()"))
s.close()
