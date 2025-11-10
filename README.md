# codecrafters-http-server-python — Simple HTTP server

Small educational HTTP server implemented in `app/main.py`. Use for learning HTTP basics and simple file operations.

## Features (complete)
- Server configuration
  - Default host: `localhost`, port: `4221`
  - Stores files under a directory (default `tmp` or passed via CLI)
  - Basic request size limit (`self.max_request_size`) and socket timeout (`self.time_out`)

- Logging
  - Logs to console (stdout) and to `server.log` (append)
  - Uses Python `logging` for informational and error messages

- Connection handling
  - Persistent (keep-alive) connections by default
  - If you do NOT want a persistent connection, include the header `Connection: close` in your request
  - Thread-per-connection handling (can be refactored to a thread pool)

- Supported endpoints
  - GET /
    - Responds with 200 OK (no body)
  - GET /echo/<text>
    - Echoes the provided text in the path
    - If the client sends `Accept-Encoding: gzip`, the server may send a gzipped response with `Content-Encoding: gzip`
  - GET /user-agent
    - Returns the value of the `User-Agent` request header as plain text
  - GET /files/<name>
    - Returns the requested file from the server directory (binary safe)
    - Uses guessed MIME type or `application/octet-stream`
    - Returns 404 if file not found
  - POST /files/<name>
    - Creates/overwrites a file with the request body under the server directory
    - Uses `Content-Length` to read body; returns 201 Created on success
    - Returns 400/403/500 for bad requests, forbidden paths, or server errors

- Safety & validation
  - Path validation to reduce directory traversal risk (`validate_path`)
  - Basic header parsing and checks for `Connection`, `Content-Length`, `Accept-Encoding`, etc.

## Usage (Windows)
From project root:
- Default directory (`tmp`):
  python app\main.py

- Custom directory (current code reads `sys.argv[2]`):
  python app\main.py ignore my_files_dir

If the port is already in use (OSError 10048), stop the other process or choose a different port.

## Request examples (curl)

- GET root:
  curl -v http://localhost:4221/

- Echo (plain):
  curl -v http://localhost:4221/echo/hello%20world

- Echo (gzip accepted):
  curl -v -H "Accept-Encoding: gzip" http://localhost:4221/echo/hello

- User-Agent:
  curl -v http://localhost:4221/user-agent

- Upload file (POST):
  curl -v --data-binary @localfile.txt http://localhost:4221/files/remote.txt

- Download file:
  curl -v http://localhost:4221/files/remote.txt -o out.txt

- Force connection close (no persistent connection):
  curl -v -H "Connection: close" http://localhost:4221/



## Troubleshooting
- Port in use (Windows):
  netstat -ano | findstr :4221
  taskkill /PID <pid> /F

- Check `server.log` and console output for runtime errors.

## License
Example/learning code — adapt and harden before production use.
