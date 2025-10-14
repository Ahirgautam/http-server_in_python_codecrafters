import socket  # noqa: F401


def main():
    
    print("Logs from your program will appear here!")

    
    server_socket = socket.create_server(("localhost", 4221))
    server_socket.accept() 


if __name__ == "__main__":
    main()
