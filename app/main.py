import socket  # noqa: F401


def main():
    
    print("Logs from your program will appear here!")

    
    server_socket = socket.create_server(("localhost", 4221))
    print("listening to port 5000")

    while True:
        
        conn, addr = server_socket.accept()
        print("Received connection ", addr)

        data = conn.recv(1024).decode("utf-8")
        print("Request received : ")
        print(data)

        response = ("HTTP/1.1 200 OK \r\n")
        conn.sendall(response.encode())
        conn.close()

if __name__ == "__main__":
    main()
