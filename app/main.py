import socket  
import threading
import sys
import os

def parse_headers(data):
    headers = {}
    header_lines = data.split("\r\n")

    for line in header_lines:
        if ":" in line:
            k,v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return headers

def handle_client(conn, addr):
    data = conn.recv(1024).decode("utf-8")
    first_line = data.split("\r\n")[0]
    method, path, _ = first_line.split(" ")
    print(f"Client {addr} -> {method} {path}")

    if(method == "GET"):
        do_get(conn, data, path)
    elif(method == "POST"):
        do_post(conn, data, path)

def do_post(conn, data, path):
    request_data = data.split("\r\n")[-1]
    res = ""
    isSend = False

    res = "HTTP/1.1 404 Not Found\r\n\r\n"
    if(path.startswith("/files")):
        file_name = path.split("/")[2]
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir,"..","files", file_name)
        file_path = os.path.abspath(file_path)

        print(file_path)
        if(not os.path.isfile(file_path)):
            try:
                with open(file_path, "w") as file:
                    file.write(request_data)
                res = "HTTP/1.1 201 Created\r\n\r\n"
            except:
                res = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
            
        
            
    if(not isSend):
        conn.sendall(res.encode())
    conn.close()


def do_get(conn, data, path):
    try:
            
        res = ""
        isSend = False
        if(path == "/"):
            res = "HTTP/1.1 200 OK\r\n\r\n"
        elif(path.startswith("/echo")):
            body = path.split("/")[2]
            res = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\n"
                "\r\n"
                f"{body}"
            )
        elif(path.startswith("/user-agent")):
            headers = parse_headers(data)
            user_agent = headers["user-agent"]
            
            res = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(user_agent)}\r\n"
                "\r\n"
                f"{user_agent}"
            )
        elif(path.startswith("/files")):
            file = path.split("/")[2]
            dir = sys.argv[2]
            
            filepath = os.path.join(dir, file)

            print(filepath)
            if os.path.isfile(filepath):
                with open(filepath,"rb") as f:
                    content = f.read()
                res = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/octet-stream\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    "\r\n"
                    
                )
                conn.sendall(res.encode() + content)
                isSend = True
            else:
                res = "HTTP/1.1 404 Not Found\r\n\r\n"
        else:
            res = "HTTP/1.1 404 Not Found\r\n\r\n"
        
        if(not isSend):
            conn.sendall(res.encode())
        conn.close()
    except Exception as e:
        print("error : ", e)
    finally:
        conn.close()


def main():
    server_socket = socket.create_server(("localhost", 4221))
    server_socket.settimeout(1)
    
    

    print("listening to port 4221")

    while True:
        try:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn,addr))
            thread.start()
        except TimeoutError:
            pass
        except KeyboardInterrupt:
            server_socket.close()
            sys.exit()
            
        

if __name__ == "__main__":
    main()
