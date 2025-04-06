import socket  # noqa: F401
import threading
import argparse
import os

HOST = "localhost"
PORT = 4221


def handle_post_request():
    pass


def handle_client(conn, addr, file_directory):
    data = conn.recv(1024)
    received_request = data.decode()
    lines = received_request.split("\r\n")
    first_line = lines[0]
    method, path, version = first_line.split(" ")

    # print(lines)
    headers = {}
    for header_part in lines[1:]:
        if header_part == "":
            break
        k, v = header_part.split(":", 1)
        headers[k.strip().lower()] = v.strip()
    body_start = received_request.find("\r\n\r\n") + 4
    body = data[body_start:].decode()
    content_length = int(headers.get("content-length", 0))
    accept_encoding = headers.get("accept-encoding", "")

    while len(body) < content_length:
        body += conn.recv(content_length - len(body))

    if path == "/":
        response = "HTTP/1.1 200 OK\r\n\r\n"
    elif path.startswith("/echo/"):
        content = path[6:]
        content_length = len(content)
        if "gzip" in accept_encoding.lower():
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Encoding: gzip\r\n"
                f"Content-Length: {content_length}\r\n"
                "\r\n"  # End of headers
                f"{content}"
            )
        else:
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {content_length}\r\n"
                "\r\n"  # End of headers
                f"{content}"
            )
    elif path.startswith("/user-agent"):
        content = headers.get("user-agent")
        content_length = len(content)

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {content_length}\r\n"
            "\r\n"  # End of headers
            f"{content}"
        )
    elif path.startswith("/files/"):
        filename = path[7:]
        full_path = os.path.join(file_directory, filename)
        if method == "POST":
            with open(full_path, "wb") as file:
                file.write(body.encode())
            response = "HTTP/1.1 201 Created\r\n\r\n"
            conn.sendall(response.encode())

        if os.path.isfile(full_path):
            with open(full_path, "rb") as file:
                content = file.read()


            content_length = len(content)

            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/octet-stream\r\n"
                f"Content-Length: {content_length}\r\n"
                "\r\n"  # End of headers
                f"{content.decode()}"
            )
            conn.sendall(response.encode())
            conn.close()
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\n"

    else:
        response = "HTTP/1.1 404 Not Found\r\n\r\n"

    conn.sendall(response.encode())
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=False)
    args = parser.parse_args()
    file_directory = args.directory

    server_socket = socket.create_server((HOST, PORT), reuse_port=True)
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(
            target=handle_client, args=(conn, addr, file_directory)
        )
        thread.start()


if __name__ == "__main__":
    main()
