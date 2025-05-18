import socket

HOST = "localhost"
PORT = 5065

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
print("Esperando conexão...")
conn, _ = server.accept()

def checksum(payload):
    return sum(ord(c) for c in payload)

buffer = ""
while "\n" not in buffer:
    buffer += conn.recv(1024).decode()

modo, max_len, window = buffer.strip().split(";")
max_len = int(max_len)
window_size = int(window)

conn.send("HANDSHAKE_OK\n".encode())
expected_seq = 0
received = {}

perder_pacote = 3

while True:
    data = conn.recv(1024).decode()
    if not data:
        break

    lines = data.strip().split("\n")
    for line in lines:
        parts = {p.split('=')[0]: p.split('=')[1] for p in line.split('|')}
        seq = int(parts["seq"])
        payload = parts["data"]
        sum_recv = int(parts["sum"].replace('&', ''))

        if seq == perder_pacote:
            print(f"Pacote {seq} perdido (simulação)")
            perder_pacote = -1
            continue

        if checksum(payload) != sum_recv:
            print(f"Checksum errado seq={seq}")
            conn.send(f"NACK|{seq}\n".encode())
            continue

        if modo == "em_rajada":
            if seq == expected_seq:
                received[seq] = payload
                expected_seq += 1
                while expected_seq in received:
                    expected_seq += 1
                conn.send(f"ACK|{expected_seq}\n".encode())
                print(f"Pacote {seq} recebido e processado.")
            else:
                print(f"Pacote fora de ordem (GBN): seq={seq}, esperado={expected_seq}")
                conn.send(f"ACK|{expected_seq}\n".encode())
        else:
            if seq not in received:
                received[seq] = payload
            conn.send(f"ACK|{seq}\n".encode())
            print(f"Pacote {seq} recebido e processado.")

mensagem_final = ''.join(received[i] for i in sorted(received))
print(f"Mensagem recebida: {mensagem_final}")

conn.close()
server.close()
