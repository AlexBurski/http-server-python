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
    # print(path)

    if path == "/":
        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    else:
        conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


if __name__ == "__main__":
    main()
