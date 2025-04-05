import socket  # noqa: F401

HOST = "localhost"
PORT = 4221


def main():
    server_socket = socket.create_server((HOST, PORT), reuse_port=True)
    conn, addr = server_socket.accept()
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

    if path == "/":
        response = "HTTP/1.1 200 OK\r\n\r\n"
    elif path.startswith("/echo/"):
        content = path[6:]
        content_length = len(content)

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

    else:
        response = "HTTP/1.1 404 Not Found\r\n\r\n"

    conn.sendall(response.encode())
    conn.close()


if __name__ == "__main__":
    main()
