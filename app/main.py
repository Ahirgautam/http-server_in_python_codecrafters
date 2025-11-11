import socket  
import threading
import sys
import os
import gzip
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("server.log", "a")
    ]
)
class HTTPServer():
    def __init__(self, host='localhost', port=4221, directory='tmp'):
        self.host = host
        self.port = port
        self.directory = directory
        self.max_request_size = 1024*1024  
        self.time_out = 1 #in seconds
        logging.info(f"Listening on {self.host}:{self.port}")
    
    
    
    def handle_client(self,conn,addr):
        def receive_until_headers_end(con):
            buffer = b""
            while b"\r\n\r\n" not in buffer:
                chunk = con.recv(1024)
                if not chunk:
                    break
                buffer += chunk
            return buffer 
        try:
            while True:
                
                data = receive_until_headers_end(conn).decode("utf-8")
                if(not data): break
                headers = self.parse_headers(data)

                first_line = data.split("\r\n")[0]
                method, path, _ = first_line.split(" ")
                print(f"Client {addr} -> {method} {path}")

                if(method == "GET"):
                    self.do_get(conn, data, path,headers)
                elif(method == "POST"):
                    self.do_post(conn, data, path, headers)
                else:
                    res = self.build_response(405, "Method Not Allowed", is_connection_keep_alive=False)
                    conn.sendall(res.encode())
                    break
                if(headers.get("connection", "").lower() == "close"):
                    break
                
        except Exception as e:
            logging.error("Error in handle_client:", exc_info=e)
        finally:
            conn.close()


    def start(self):
        with socket.create_server((self.host, self.port)) as server_socket:
            server_socket.settimeout(self.time_out)
            while True:
                try:
                    conn, addr = server_socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(conn,addr))
                    thread.start()
                except TimeoutError:
                    pass

    
    def do_post(self, conn, data, path,headers):
        try:
            request_parts = data.split("\r\n\r\n", 1)
            request_data = request_parts[1] if len(request_parts) > 1  else ""
            
            is_request_persistent = not (headers.get("connection", "").lower() == "close")
            
            if(path.startswith("/files")):
                dir = os.path.join(os.path.dirname(__file__), "files")
                if not os.path.exists(dir):
                    os.makedirs(dir)
                path_parts = path.split("/", 2)
                if(len(path_parts) < 3 or not path_parts[2]):
                    res = self.build_response(status_code=400, status_message="Bad Request", is_connection_keep_alive=is_request_persistent)
                    conn.sendall(res)
                    return
                
                file_name = path_parts[2]
            
                file_path =  os.path.join(dir, file_name)
                if(not os.path.isfile(file_path)):
                    try:
                        with open(file_path, "w") as file:
                            file.write(request_data)
                        res = self.build_response(status_code=201, status_message="Created", is_connection_keep_alive=is_request_persistent)
                        conn.sendall(res)
                        return
                    except:
                        logging.error("Error writing file:", exc_info=True)
                        res = self.build_response(status_code=500, status_message="Internal Server Error", is_connection_keep_alive=is_request_persistent)
                        conn.sendall(res)
                        return
                else:
                    res = self.build_response(status_code=409, status_message="Conflict", is_connection_keep_alive=is_request_persistent)
                    conn.sendall(res)
                    return  
            
            res = self.build_response(status_code=404, status_message="Not Found", is_connection_keep_alive=is_request_persistent)
            conn.sendall(res)
        except Exception as e:
            logging.error("Error in do_post:", exc_info=e)
            try:
                conn.sendall(self.build_response(500, "Internal Server Error", is_connection_keep_alive=False))
            except Exception:
                pass   
    def do_get(self, conn, data, path, headers):
        import urllib.parse
        
        try:
                
            is_request_persistent = not (headers.get("connection","" ).lower() == "close")

            if(path == "/"):
                res = self.build_response(status_code=200, status_message="OK", is_connection_keep_alive=is_request_persistent)
                conn.sendall(res)
                return
        
            if(path.startswith("/echo")):
                path_parts = path.split("/", 2)
                body = urllib.parse.unquote_plus(path_parts[2]) if len(path_parts) > 2 else ""
                accept_enc = list(map(lambda s: s.strip(), headers.get("accept-encoding", "").split(",")))

                if("gzip" in accept_enc):
                    compressed_body = gzip.compress(body.encode("utf-8"))
                    res = self.build_response(status_code=200,status_message="OK", content_type="text/plain", content=compressed_body,is_byte_content=True,is_connection_keep_alive=is_request_persistent, content_encoding="gzip")
                    conn.sendall(res+compressed_body)
                    return
                else:
                    res = self.build_response(status_code=200, status_message="OK", content_type="text/plain", content=body, is_connection_keep_alive=is_request_persistent)
                    conn.sendall(res)
                    return
            if(path.startswith("/user-agent")):
                user_agent = headers.get("user-agent", "")
                res = self.build_response(status_code=200, status_message="OK", content_type="text/plain", content=user_agent, is_connection_keep_alive=is_request_persistent)
                conn.sendall(res)
                return
            
            if(path.startswith("/files")):
                path_parts = path.split("/", 2)
                if(len(path_parts) < 3 or not path_parts[2]):
                    res = self.build_response(status_code=400, status_message="Bad Request", is_connection_keep_alive=is_request_persistent)
                    conn.sendall(res)
                    return
                
                file = urllib.parse.unquote_plus(path_parts[2])
                dir = sys.argv[2] if len(sys.argv) > 2 else "tmp"
                
                filepath = os.path.join(dir, file)
               
                if os.path.isfile(filepath) and self.validate_path(filepath, dir):
                    with open(filepath,"rb") as f:
                        content = f.read()
                    res = self.build_response(status_code=200, status_message="OK", content_type="application/octet-stream", content=content, is_byte_content=True, is_connection_keep_alive=is_request_persistent)
                    conn.sendall(res + content)
                    return
                else:
                    print("no no no")
                    res = self.build_response(status_code=404, status_message="Not Found", is_connection_keep_alive=is_request_persistent)
                    conn.sendall(res)
                    return
            else:
                res = self.build_response(status_code=404, status_message="Not Found", is_connection_keep_alive=is_request_persistent)
                conn.sendall(res)    
            
        except Exception as e:
            print("error : ", e)
        

    def build_response(self,status_code, status_message, content_type = None, content = None, is_connection_keep_alive = True, is_byte_content = False,content_encoding=None):
        if(content is not None):
            res = ( 
                f"HTTP/1.1 {status_code} {status_message}\r\n"
                f"{f'Content-Encoding: {content_encoding}\r\n' if content_encoding else ''}"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(content)}\r\n"
                f'Connection: {"keep-alive" if is_connection_keep_alive else "close"}\r\n'
                "\r\n"
            )
            
            if(not is_byte_content):
                res += f"{content}"
            return res.encode()

        res = (
            f"HTTP/1.1 {status_code} {status_message}\r\n"
            f'Connection: {"keep-alive" if is_connection_keep_alive else "close"}\r\n'
            "Content-Length: 0\r\n"
            "\r\n"
        )
        return res.encode()
    def parse_headers(self,data):
        headers = {}
        header_lines = data.split("\r\n")

        for line in header_lines:
            if ":" in line:
                k,v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        return headers
    def validate_path(self, path, directory):
            """Validate and sanitize the requested file path to prevent directory traversal attacks."""
            requested_path = Path(path).resolve()
            base_directory = Path(directory).resolve()
            return requested_path.is_relative_to(base_directory)


def main():
    try:
        
        dir = sys.argv[2] if len(sys.argv) > 2 else "tmp"
        if not os.path.exists(dir):
            os.makedirs(dir)
        server = HTTPServer(host='localhost', port=4221, directory=dir)
        server.start()    
                
    except KeyboardInterrupt:
        logging.info("Closing server")
        sys.exit()
            
        

if __name__ == "__main__":
    main()
