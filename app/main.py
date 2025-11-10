import socket  
import threading
import sys
import os
import gzip



def build_response(status_code, status_message, content_type = None, content = None, is_connection_keep_alive = True, is_byte_content = False,content_encoding=None):
    if(content):
        res = (
            f"HTTP/1.1 {status_code} {status_message}\r\n"
            f"{f'Content-Encoding: {content_encoding}\r\n' if content_encoding else ''}"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(content)}\r\n"
            f"Connection: {"keep-alive" if is_connection_keep_alive else "close"}\r\n"
            "\r\n"
        )
        
        if(not is_byte_content):
            res += f"{content}"
        return res

    res = (
        f"HTTP/1.1 {status_code} {status_message}\r\n"
        f"Connection: {"keep-alive" if is_connection_keep_alive else "close"}\r\n"
        "\r\n"
    )
    return res
     
def parse_headers(data):
    headers = {}
    header_lines = data.split("\r\n")

    for line in header_lines:
        if ":" in line:
            k,v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return headers

def handle_client(conn, addr):
    try:
        while True:
            data = conn.recv(1024).decode("utf-8")
            if(not data): break
            headers = parse_headers(data)

            first_line = data.split("\r\n")[0]
            method, path, _ = first_line.split(" ")
            print(f"Client {addr} -> {method} {path}")

            if(method == "GET"):
                do_get(conn, data, path,headers)
            elif(method == "POST"):
                do_post(conn, data, path, headers)
            else:
                res = build_response(405, "Method Not Allowed", is_connection_keep_alive=False)
                conn.sendall(res.encode())
                break
            if(headers.get("connection", "").lower() == "close"):
                break
    except Exception as e:
        print("Error in handle_client:", e)
    finally:
        conn.close()

def do_post(conn, data, path,headers):
    request_data = data.split("\r\n")[-1]
    res = ""
    is_reponse_sent = False
    
    is_request_persistent = not (headers.get("connection", "").lower() == "close")
    res = build_response(status_code=404, status_message="Not Found", is_connection_keep_alive=is_request_persistent)
    
    if(path.startswith("/files")):
        file_name = path.split("/")[2]
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir,"..","files", file_name)
        file_path = os.path.abspath(file_path)

        if(not os.path.isfile(file_path)):
            try:
                with open(file_path, "w") as file:
                    file.write(request_data)
                res = build_response(status_code=201, status_message="Created", is_connection_keep_alive=is_request_persistent)
            except:
                res = build_response(status_code=500, status_message="Internal Server Error", is_connection_keep_alive=is_request_persistent)
            
    if(not is_reponse_sent):
        conn.sendall(res.encode())
    
def do_get(conn, data, path, headers):
    try:
            
        res = ""
        is_reponse_sent = False
        is_request_persistent = not (headers.get("connection","" ).lower() == "close")

        if(path == "/"):
            res = build_response(status_code=200, status_message="OK", is_connection_keep_alive=is_request_persistent)
            
        elif(path.startswith("/echo")):
            body = path.split("/")[2]
            encoding_formates = list(map(lambda s: s.strip(), headers.get("accept-encoding", "").split(",")))

            if(encoding_formates.count("gzip") > 0):
                compressed_body = gzip.compress(body.encode("utf-8"))
                

                res = build_response(status_code=200,status_message="OK", content_type="text/plain", content=compressed_body,is_byte_content=True,is_connection_keep_alive=is_request_persistent, content_encoding="gzip")
                conn.sendall(res.encode()+compressed_body)
                is_reponse_sent = True
            else:
                res = build_response(status_code=200, status_message="OK", content_type="text/plain", content=body, is_connection_keep_alive=is_request_persistent)
            
        elif(path.startswith("/user-agent")):
            
            user_agent = headers["user-agent"]
            res = build_response(status_code=200, status_message="OK", content_type="text/plain", content=user_agent, is_connection_keep_alive=is_request_persistent)
        elif(path.startswith("/files")):
            file = path.split("/")[2]
            dir = sys.argv[2] if len(sys.argv) > 1 else "tmp"
            
            filepath = os.path.join(dir, file)

            print(filepath)
            if os.path.isfile(filepath):
                with open(filepath,"rb") as f:
                    content = f.read()
                res = build_response(status_code=200, status_message="OK", content_type="application/octet-stream", content=content, is_byte_content=True, is_connection_keep_alive=is_request_persistent)
                conn.sendall(res.encode() + content)
                is_reponse_sent = True
            else:
                res = build_response(status_code=404, status_message="Not Found", is_connection_keep_alive=is_request_persistent)
            
        else:
            res = build_response(status_code=404, status_message="Not Found", is_connection_keep_alive=is_request_persistent)
            
        
        if(not is_reponse_sent):
            conn.sendall(res.encode())
        
    except Exception as e:
        print("error : ", e)
    


def main():
    try:
        server_socket = socket.create_server(("localhost", 4221))
        #Change this if persistent request dont work
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
        print("Closing server")
        sys.exit()
            
        

if __name__ == "__main__":
    main()
