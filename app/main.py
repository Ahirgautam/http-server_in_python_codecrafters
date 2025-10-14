import socket  # noqa: F401


def main():
    
    print("Logs from your program will appear here!")

    
    server_socket = socket.create_server(("localhost", 4221))
    print("listening to port 5000")

    while True:
        
        conn, addr = server_socket.accept()
        #print("Received connection ", addr)

        data = conn.recv(1024).decode("utf-8")
        first_line = data.split("\r\n")[0]

        method, path, _ = first_line.split(" ")
        print("Path :")
        print(path)

        if(path == "/"):
            res = "HTTP/1.1 200 OK\r\n\r\n"
        else:
            res = "HTTP/1.1 404 Not Found\r\n\r\n"
        
        
        conn.sendall(res.encode())
        conn.close()

if __name__ == "__main__":
    main()
