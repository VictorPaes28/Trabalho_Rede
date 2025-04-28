import socket
import threading
import time
import random

def calcular_checksum(dados):
    return str(sum(ord(c) for c in dados) % 256)

HOST = "localhost"
PORT = 12345

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

modo = "lote"
tamanho = 3
handshake = f"modo:{modo};tamanho:{tamanho}"
cliente.send(handshake.encode())
print(f"[HANDSHAKE ENVIADO]: {handshake}")

modo_operacao = input("Escolha o modo (gbn ou sr): ").strip()
cliente.send(modo_operacao.encode())
print(f"[MODO OPERACAO ENVIADO]: {modo_operacao}")

mensagem = input("Digite a mensagem para enviar: ")

pacotes = []
for i in range(0, len(mensagem), tamanho):
    dados = mensagem[i:i+tamanho]
    checksum = calcular_checksum(dados)
    pacotes.append(f"{i//tamanho}|{dados}|{checksum}")

janela_tamanho = 4
base = 0
next_seq = 0
timeout = 3
acks_recebidos = set()
lock = threading.Lock()
timer = None

perder_pacote = input("Deseja simular perda de pacote? (s/n): ").strip().lower() == 's'
if perder_pacote:
    pacote_perdido = int(input("Digite o número do pacote que será perdido: "))
else:
    pacote_perdido = None

def iniciar_timer():
    global timer
    if timer:
        timer.cancel()
    timer = threading.Timer(timeout, tratar_timeout)
    timer.start()

def tratar_timeout():
    with lock:
        print("[TIMEOUT] Reenviando pacotes da janela")
        for i in range(base, next_seq):
            print(f"[REENVIANDO]: {pacotes[i]}")
            cliente.send(pacotes[i].encode())
        iniciar_timer()

def receber_ack():
    global base
    while True:
        try:
            resposta = cliente.recv(1024).decode()
            print(f"[ACK RECEBIDO]: {resposta}")
            if resposta.startswith("ACK"):
                seq_ack = int(resposta.split()[1])
                with lock:
                    if seq_ack >= base:
                        base = seq_ack + 1
                        if base == next_seq:
                            if timer:
                                timer.cancel()
                        else:
                            iniciar_timer()
        except:
            break

threading.Thread(target=receber_ack, daemon=True).start()

while base < len(pacotes):
    with lock:
        while next_seq < base + janela_tamanho and next_seq < len(pacotes):
            if perder_pacote and next_seq == pacote_perdido:
                print(f"[SIMULADO PERDA]: Pacote {next_seq}")
                next_seq += 1
                continue
            print(f"[PACOTE ENVIADO]: {pacotes[next_seq]}")
            cliente.send(pacotes[next_seq].encode())
            if base == next_seq:
                iniciar_timer()
            next_seq += 1
    time.sleep(0.1)

if timer:
    timer.cancel()

cliente.send("FIM".encode())
print("[FIM ENVIADO]")

cliente.close()
