import socket
import threading
import argparse
import os
import gzip

HOST = "localhost"
PORT = 4221


def parse_http_request(conn):
    """
    Reads the raw HTTP request from the connection and returns
    the method, path, HTTP version, headers (dict), and body (bytes).
    """
    data = conn.recv(1024)
    if not data:
        return None, None, None, {}, b""

    header_end = data.find(b"\r\n\r\n")
    if header_end == -1:
        return None, None, None, {}, b""

    header_part = data[:header_end].decode("utf-8", errors="replace")
    body_part = data[header_end + 4:]
    lines = header_part.split("\r\n")
    try:
        method, path, version = lines[0].split(" ")
    except ValueError:
        return None, None, None, {}, b""

    headers = {}
    for line in lines[1:]:
        if not line.strip():
            break
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()

    content_length = int(headers.get("content-length", 0))

    while len(body_part) < content_length:
        chunk = conn.recv(content_length - len(body_part))
        if not chunk:
            break
        body_part += chunk

    return method, path, version, headers, body_part


def build_response(status_line, headers=None, body=b""):
    """
    Helper to build an HTTP response from a status line (e.g. "HTTP/1.1 200 OK"),
    optional dictionary of headers, and a raw body (bytes).
    Returns the raw HTTP response as bytes.
    """
    if headers is None:
        headers = {}

    header_str = ""
    for key, value in headers.items():
        header_str += f"{key}: {value}\r\n"

    response = f"{status_line}\r\n" f"{header_str}\r\n".encode("utf-8") + body
    return response


def handle_request(method, path, headers, body, file_directory):
    """
    Given all request details, decide how to respond.
    Returns a bytes object with the complete HTTP response.
    """
    if path == "/":
        return build_response(
            "HTTP/1.1 200 OK",
            {"Content-Type": "text/plain", "Content-Length": "0"},
            b"",
        )

    elif path.startswith("/echo/"):
        content = path[len("/echo/"):]
        accept_encoding = headers.get("accept-encoding", "").lower()

        if "gzip" in [enc.strip() for enc in accept_encoding.split(",")]:
            compressed_body = gzip.compress(content.encode("utf-8"))
            return build_response(
                "HTTP/1.1 200 OK",
                {
                    "Content-Type": "text/plain",
                    "Content-Encoding": "gzip",
                    "Content-Length": str(len(compressed_body)),
                },
                compressed_body,
            )
        else:
            return build_response(
                "HTTP/1.1 200 OK",
                {"Content-Type": "text/plain", "Content-Length": str(len(content))},
                content.encode("utf-8"),
            )

    elif path.startswith("/user-agent"):
        user_agent = headers.get("user-agent", "")
        return build_response(
            "HTTP/1.1 200 OK",
            {"Content-Type": "text/plain", "Content-Length": str(len(user_agent))},
            user_agent.encode("utf-8"),
        )

    elif path.startswith("/files/"):
        filename = path[len("/files/"):]
        if not file_directory:
            return build_response("HTTP/1.1 404 Not Found")

        full_path = os.path.join(file_directory, filename)

        if method == "POST":
            with open(full_path, "wb") as f:
                f.write(body)
            return build_response("HTTP/1.1 201 Created")

        if os.path.isfile(full_path):
            with open(full_path, "rb") as f:
                content = f.read()
            return build_response(
                "HTTP/1.1 200 OK",
                {
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(len(content)),
                },
                content,
            )
        else:
            return build_response("HTTP/1.1 404 Not Found")

    return build_response("HTTP/1.1 404 Not Found")


def handle_client(conn, file_directory):
    """
    Reads request from a client connection, processes it, and sends back a response.
    """
    try:
        method, path, version, headers, body = parse_http_request(conn)
        if not method:
            response = build_response("HTTP/1.1 400 Bad Request")
        else:
            response = handle_request(
                method, path, headers, body, file_directory
            )
        conn.sendall(response)
    except Exception as e:
        error_message = f"Internal Server Error: {str(e)}"
        response = build_response(
            "HTTP/1.1 500 Internal Server Error",
            {"Content-Type": "text/plain", "Content-Length": str(len(error_message))},
            error_message.encode("utf-8"),
        )
        conn.sendall(response)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=False, default=".")
    args = parser.parse_args()
    file_directory = args.directory

    with socket.create_server((HOST, PORT), reuse_port=True) as server_socket:
        print(f"Serving on {HOST}:{PORT}, directory={file_directory}")
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(
                target=handle_client, args=(conn, file_directory), daemon=True
            )
            thread.start()


if __name__ == "__main__":
    main()
