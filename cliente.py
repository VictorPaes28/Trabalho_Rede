import socket
import math
import time 

HOST = "localhost"
PORT = 1234
TIMEOUT = 1

modes = ["em_rajada", "individual"]
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))
cliente.settimeout(TIMEOUT)

def calcular_checksum(payload):
    return sum(ord(c) for c in payload)

tipo = None
while True:
    try:
        mode_code = int(input(
            "Digite [1] para Go-Back-N\n"
            "Digite [2] para Selective Repeat\n"
            "Sua escolha: "
        ))
        if mode_code not in [1, 2]:
            print("\nDigite apenas 1 ou 2\n")
        else:
            tipo = modes[mode_code - 1]
            break
    except ValueError:
        print("\nEntrada inválida\n")

max_length = 0
while True:
    try:
        max_length = int(input("Tamanho máximo (1 a 3): "))
        if not 1 <= max_length <= 3:
            print("\nValor precisa estar entre 1 e 3\n")
        else:
            break
    except ValueError:
        print("\nEntrada inválida\n")

window_size = 4  

data = f"{tipo};{max_length};{window_size}\n"
cliente.send(data.encode())
print(f"[C] Handshake enviado: modo={tipo}, tam={max_length}, win={window_size}")
confirmation = cliente.recv(1024).decode().strip()
print(f"[C] Confirmação recebida: {confirmation}\n")

texto = input("Mensagem: ")
num_packets = math.ceil(len(texto) / max_length)

base = 0
next_seq = 0
acked = [False] * num_packets  
acksRecebidos = []
finished = False

while not finished and len(acksRecebidos) < num_packets:
    
    while next_seq < num_packets and next_seq < base + window_size:
        start = next_seq * max_length
        payload = texto[start:start + max_length]
        checksum = calcular_checksum(payload)
        if next_seq + 1 == num_packets and tipo == "em_rajada":
            packet = f"seq={next_seq}|data={payload}|sum={checksum}&\n"
        else:
            packet = f"seq={next_seq}|data={payload}|sum={checksum}\n"

        cliente.send(packet.encode())
        inicio = time.time()
        print(f"[C] Pacote enviado: {packet.strip()}\n")
        if base == next_seq:
            timer_start = time.time()
        next_seq += 1

    try:
        data = cliente.recv(1024).decode()
        for ack_msg in data.splitlines():
            fim = time.time()
            tempo_execucao = fim - inicio

            if ack_msg.startswith("ACK"):
                window_size += 1
                print(f"[C] Recebido ACK: {ack_msg}")
                print(f"[C] RTT: {tempo_execucao:.3f}s\n")

                ack_seq = int(ack_msg.split("|")[1])

                if tipo == "em_rajada":
                    ack_seq = int(ack_msg.split("|")[1])
                    base = ack_seq + 1
                    if base == num_packets:
                        finished = True
                else:
                    if not acked[ack_seq]:
                        acked[ack_seq] = True
                        acksRecebidos.append(ack_seq)
                    while base < num_packets and acked[base]:
                        base += 1

            else:
                print(f"[C] Recebido NACK: {ack_msg}")
                print("[C] Servidor congestionado")
                finished = True

    except socket.timeout:
        if finished:
            break
        print(f"[C] Timeout! Reenviando janela a partir de {base}")
        if tipo == "em_rajada":
            for seq in range(base, min(base + window_size, num_packets)):
                start = seq * max_length
                payload = texto[start:start + max_length]
                checksum = calcular_checksum(payload)
                packet = f"seq={seq}|data={payload}|sum={checksum}\n"
                cliente.send(packet.encode())
                print(f"[C] Reenviado: {packet.strip()}")
        else:
            for seq in range(base, min(base + window_size, num_packets)):
                if acked[seq]:
                    continue
                start = seq * max_length
                payload = texto[start:start + max_length]
                checksum = calcular_checksum(payload)
                packet = f"seq={seq}|data={payload}|sum={checksum}\n"
                cliente.send(packet.encode())
                print(f"[C] Reenviado: {packet.strip()}")
        print()
        inicio = time.time()

cliente.close()
print("[C] Conexão encerrada.")