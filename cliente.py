import socket
import math
import time

HOST = "localhost"
PORT = 5065
TIMEOUT = 2

modes = ["em_rajada", "individual"]
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
client.settimeout(TIMEOUT)

def calcular_checksum(payload):
    return sum(ord(c) for c in payload)

tipo = None
while True:
    try:
        mode_code = int(input(
            "Digite 1 para o modo Em Rajada (Go-Back-N)\n"
            "Digite 2 para o modo Individual (Repetição Seletiva)\n"
            "Digite: "
        ))
        if mode_code not in [1, 2]:
            print("\nDigite apenas 1 ou 2\n")
        else:
            tipo = modes[mode_code - 1]
            break
    except ValueError:
        print("\nEntrada inválida. Digite um número\n")

max_length = 0
while True:
    try:
        max_length = int(input("Digite o tamanho máximo da mensagem (ex: 5-10): "))
        if not 1 <= max_length <= 50:
            print("\nTamanho fora do intervalo (1-50)\n")
        else:
            break
    except ValueError:
        print("\nEntrada inválida. Digite um número\n")

window_size = 4

data = f"{tipo};{max_length};{window_size}\n"
client.send(data.encode())
print(f"[CLIENTE] Handshake enviado: modo={tipo}, max_length={max_length}, janela={window_size}")
confirmation = client.recv(1024).decode().strip()
print(f"[CLIENTE] Confirmação recebida: {confirmation}\n")

texto = input("Digite a mensagem a ser enviada: ")
num_packets = math.ceil(len(texto) / max_length)

base = 0
next_seq = 0
acked = [False] * num_packets
timer_start = None
acksRecebidos = []
finished = False

while not finished and len(acksRecebidos) < num_packets:
    while next_seq < num_packets and next_seq < base + window_size:
        start = next_seq * max_length
        payload = texto[start:start + max_length]
        checksum = calcular_checksum(payload)

        # Simula erro no pacote 2
        if next_seq == 2:
            checksum += 1

        if next_seq + 1 == num_packets and tipo == "em_rajada":
            packet = f"seq={next_seq}|data={payload}|sum={checksum}&\n"
        else:
            packet = f"seq={next_seq}|data={payload}|sum={checksum}\n"

        client.send(packet.encode())
        print(f"[CLIENTE] Pacote enviado: {packet.strip()}\n")

        if base == next_seq:
            timer_start = time.time()
        next_seq += 1

    try:
        data = client.recv(1024).decode()
        for ack_msg in data.splitlines():
            if ack_msg.startswith("ACK"):
                ack_value = int(ack_msg.split("|")[1])
                print(f"[CLIENTE] ACK recebido: {ack_msg}")

                if tipo == "em_rajada" and ack_value == num_packets:
                    finished = True
                    break

                if tipo == "em_rajada":
                    if ack_value not in acksRecebidos:
                        acksRecebidos.append(ack_value)
                else:
                    if not acked[ack_value]:
                        acked[ack_value] = True
                        acksRecebidos.append(ack_value)

                if tipo == "individual":
                    while base < num_packets and acked[base]:
                        base += 1
                else:
                    base = ack_value

                if base == next_seq:
                    timer_start = None
                else:
                    timer_start = time.time()

            elif ack_msg.startswith("NACK"):
                print(f"[CLIENTE] NACK recebido: {ack_msg}")
                nack_seq = int(ack_msg.split("|")[1])
                next_seq = nack_seq
                break

    except socket.timeout:
        print(f"[CLIENTE] Timeout. Reenviando janela base={base}")
        next_seq = base

client.close()
print("[CLIENTE] Conexão encerrada.")
