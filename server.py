import socket
import struct
import pickle
import threading

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 9999))
server_socket.listen(4)

clients_connected = {}
clients_data = {}
count = 1


def connection_requests():
    global count
    while True:
        print("Waiting for connection...")
        client_socket, address = server_socket.accept()

        print(f"Connections from {address} has been established")
        print(len(clients_connected))
        if len(clients_connected) == 4:
            client_socket.send('not_allowed'.encode())
            client_socket.close()
            continue
        else:
            client_socket.send('allowed'.encode())

        try:
            client_name = client_socket.recv(1024).decode('utf-8')
        except:
            print(f"{address} disconnected")
            client_socket.close()
            continue

        print(f"{address} identified itself as {client_name}")

        clients_connected[client_socket] = (client_name, count)

        image_size_bytes = client_socket.recv(1024)
        image_size_int = struct.unpack('i', image_size_bytes)[0]

        client_socket.send('received'.encode())
        image_extension = client_socket.recv(1024).decode()

        b = b''
        while True:
            image_bytes = client_socket.recv(1024)
            b += image_bytes
            if len(b) == image_size_int:
                break

        clients_data[count] = (client_name, b, image_extension)

        clients_data_bytes = pickle.dumps(clients_data)
        clients_data_length = struct.pack('i', len(clients_data_bytes))

        client_socket.send(clients_data_length)
        client_socket.send(clients_data_bytes)

        if client_socket.recv(1024).decode() == 'image_received':
            client_socket.send(struct.pack('i', count))

            for client in clients_connected:
                if client != client_socket:
                    client.send('notification'.encode())
                    data = pickle.dumps(
                        {'message': f"{clients_connected[client_socket][0]} joined the chat", 'extension': image_extension,
                         'image_bytes': b, 'name': clients_connected[client_socket][0], 'n_type': 'joined', 'id': count})
                    data_length_bytes = struct.pack('i', len(data))
                    client.send(data_length_bytes)
                    client.send(data)
        count += 1
        t = threading.Thread(target=receive_data, args=(client_socket,))
        t.start()

def receive_data(client_socket):
    while True:
        try:
            data_type = client_socket.recv(1024).decode()
            
            if data_type == 'file':
                size_data = client_socket.recv(4)
                size = struct.unpack('!I', size_data)[0]
                
                file_data = b''
                while len(file_data) < size:
                    chunk = client_socket.recv(min(1024, size - len(file_data)))
                    if not chunk:
                        raise ConnectionError("Connection closed while receiving file")
                    file_data += chunk
                
                for client in clients_connected:
                    if client != client_socket:
                        client.send('file'.encode())
                        client.send(struct.pack('!I', size))
                        client.send(file_data)
            
            elif data_type == 'message':
                data_bytes = client_socket.recv(1024)
                for client in clients_connected:
                    if client != client_socket:
                        client.send('message'.encode())
                        client.send(data_bytes)
            
        except ConnectionResetError:
            handle_client_disconnect(client_socket)
            break
        except ConnectionAbortedError:
            handle_client_disconnect(client_socket)
            break
        except Exception as e:
            print(f"Error handling client {clients_connected[client_socket][0]}: {e}")
            handle_client_disconnect(client_socket)
            break

def handle_client_disconnect(client_socket):
    print(f"{clients_connected[client_socket][0]} disconnected")
    
    for client in clients_connected:
        if client != client_socket:
            client.send('notification'.encode())
            data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                 'id': clients_connected[client_socket][1], 'n_type': 'left'})
            data_length_bytes = struct.pack('i', len(data))
            client.send(data_length_bytes)
            client.send(data)

    del clients_data[clients_connected[client_socket][1]]
    del clients_connected[client_socket]
    client_socket.close()

if __name__ == "__main__":
    try:
        print("Server is starting...")
        connection_requests()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Server is shutting down...")
        server_socket.close()
