import socket
import math
import time

HOST = "localhost"
PORT = 5065
TIMEOUT = 2

modes = ["em_rajada", "individual"]

print("[CLIENTE] Aguardando servidor estar pronto... (SÓ EXECUTE O CLIENTE APÓS '[SERVIDOR] Aguardando conexão...')")
time.sleep(1)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
client.settimeout(TIMEOUT)

def calcular_checksum(payload):
    return sum(ord(c) for c in payload)

print("[CLIENTE] Conectado ao servidor.")

while True:
    try:
        mode_code = int(input("Digite 1 para o modo Em Rajada (Go-Back-N)\nDigite 2 para o modo Individual (Repetição Seletiva)\nDigite: "))
        if mode_code in [1, 2]:
            tipo = modes[mode_code - 1]
            break
        else:
            print("Digite 1 ou 2.")
    except ValueError:
        print("Entrada inválida.")

while True:
    try:
        max_length = int(input("Digite o tamanho máximo da mensagem (mínimo recomendado: 3): "))
        if max_length >= 1:
            break
        else:
            print("Valor deve ser maior que 0.")
    except ValueError:
        print("Entrada inválida.")

window_size = 4

data = f"{tipo};{max_length};{window_size}\n"
client.send(data.encode())
print(f"[CLIENTE] Handshake enviado: modo={tipo}, max_length={max_length}, janela={window_size}")
confirmation = client.recv(1024).decode().strip()
print(f"[CLIENTE] Confirmação recebida: {confirmation}\n")

texto = input("Digite uma mensagem longa para teste (ex: pelo menos 15 caracteres): ")
num_packets = math.ceil(len(texto) / max_length)

print("\n[CLIENTE] Escolha o tipo de simulação:")
print("1 - Simular perda de integridade (checksum corrompido em seq=2)")
print("2 - Simular pacote fora de ordem (troca seq=1 e seq=2)")
print("3 - Simular timeout (servidor ignorará um pacote)")
print("0 - Sem simulação")
sim_opcao = int(input("Escolha: "))

base = 0
next_seq = 0
acked = [False] * num_packets
timer_start = None
acksRecebidos = []
finished = False
packets = []

for i in range(num_packets):
    start = i * max_length
    payload = texto[start:start + max_length]
    checksum = calcular_checksum(payload)
    if i == num_packets - 1 and tipo == "em_rajada":
        packet = f"seq={i}|data={payload}|sum={checksum}&\n"
    else:
        packet = f"seq={i}|data={payload}|sum={checksum}\n"
    packets.append((i, packet, payload, checksum))

if sim_opcao == 1:
    for idx in range(len(packets)):
        if packets[idx][0] == 2:
            corrompido = packets[idx][3] + 1
            payload = packets[idx][2]
            packet = f"seq=2|data={payload}|sum={corrompido}\n"
            packets[idx] = (2, packet, payload, corrompido)
elif sim_opcao == 2:
    if num_packets > 2:
        packets[1], packets[2] = packets[2], packets[1]

while not finished and len(acksRecebidos) < num_packets:
    while next_seq < num_packets and next_seq < base + window_size:
        seq, packet, _, _ = packets[next_seq]
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