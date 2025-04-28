import socket

HOST = "localhost"
PORT = 1234

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORT))
servidor.listen(1)
print(f"[S] Aguardando conexão na porta {PORT}...")
conn, addr = servidor.accept()
print(f"[S] Conectado a {addr}")

def calcular_checksum(payload):
    return sum(ord(c) for c in payload)

opc = input("Digite [1] para simular perda ou [2] para normal: ")
if opc == "1":
    perderPacote = True
    pacotePerdido = int(input("Número do pacote que será perdido: "))
else:
    perderPacote = False
    pacotePerdido = -1

buffer = ""
while "\n" not in buffer:
    buffer += conn.recv(1024).decode()

header, buffer = buffer.split("\n", 1)
mode, max_len_str, window_str = header.split(";")
max_length = int(max_len_str)
window_size = int(window_str)
print(f"[S] Handshake: modo={mode}, max={max_length}, win={window_size}\n")
conn.send("HANDSHAKE_OK\n".encode())

expected_seq = 0
received = {}

while True:
    data = conn.recv(1024).decode()
    if not data:
        break
    buffer += data
    
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        if "&" in line:
            lastPacket = True
            line = line.replace("&", "")
        else:
            lastPacket = False

        parts = line.strip().split("|")
        d = {k:v for k,v in (p.split("=",1) for p in parts)}
        seq = int(d["seq"])
        payload = d["data"]
        checksum_recv = int(d["sum"])

        if perderPacote and seq == pacotePerdido:
            print(f"[S] Simulando perda do pacote {seq}")
            perderPacote = False
            continue

        calc = calcular_checksum(payload)
        print(f"[S] Pacote recebido seq={seq}|data={payload}|sum={calc}")

        if checksum_recv != calc:
            print(f"[S] Checksum inválido seq={seq}")
            continue

        if seq in received:
            print(f"[S] Pacote repetido seq={seq}")
            continue

        if mode == "individual":
            if seq in received:
                print(f"[S] Pacote repetido seq={seq}")
                continue

            received[seq] = payload
            ack = f"ACK|{seq}\n"
            conn.send(ack.encode())
            print(f"[S] Enviado {ack.strip()}")
        else:  
            if seq == expected_seq:
                received[seq] = payload
                conn.send(f"ACK|{seq}\n".encode())
                print(f"[S] Enviado ACK|{seq}")
                expected_seq += 1
            else:
                print(f"[S] Pacote fora de ordem seq={seq} - ignorado")
                conn.send(f"ACK|{expected_seq-1}\n".encode())
                print(f"[S] Enviado ACK|{expected_seq-1} (fora de ordem)")

        if lastPacket:
            break

msg = ''.join(received[i] for i in sorted(received))
print(f"[S] Mensagem final: '{msg}'")

conn.close()
servidor.close()
print("[S] Conexão encerrada.")