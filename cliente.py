import socket
import threading
import time

def calcular_checksum(dados):
    return str(sum(bytearray(dados.encode())) % 256)

cliente = socket.socket()
cliente.connect(("localhost", 12345))

modo = "lote"
tamanho = "3"
handshake = f"modo:{modo},tamanho:{tamanho}"
cliente.send(handshake.encode())
print(f"[HANDSHAKE ENVIADO]: {handshake}")

modo_operacao = input("Escolha o modo (GBN para Go-Back-N, SR para Selective Repeat): ").strip()
cliente.send(modo_operacao.encode())
print(f"[MODO OPERACAO ENVIADO]: {modo_operacao}")

mensagem = input("Digite a mensagem para enviar ao servidor: ")
tamanho_pacote = 3
janela_tamanho = 4
timeout = 3

pacotes = []
acks_recebidos = set()

for i in range(0, len(mensagem), tamanho_pacote):
    dados = mensagem[i:i+tamanho_pacote]
    seq = i // tamanho_pacote
    checksum = calcular_checksum(dados)
    pacote = f"{seq}|{dados}|{checksum}"
    pacotes.append(pacote)

base = 0
next_seq = 0
lock = threading.Lock()

gbn_timer = None

sr_timers = {}

def iniciar_gbn_timer():
    global gbn_timer
    if gbn_timer is not None:
        gbn_timer.cancel()
    gbn_timer = threading.Timer(timeout, gbn_timeout_handler)
    gbn_timer.start()

def gbn_timeout_handler():
    global base, next_seq
    with lock:
        print("[TIMEOUT GBN] Reenviando todos os pacotes da janela a partir do base")
        for i in range(base, next_seq):
            print(f"[REENVIANDO]: {pacotes[i]}")
            cliente.send(pacotes[i].encode())
        iniciar_gbn_timer()

def iniciar_sr_timer(seq):
    t = threading.Timer(timeout, sr_timeout_handler, args=(seq,))
    sr_timers[seq] = t
    t.start()

def sr_timeout_handler(seq):
    with lock:
        if seq not in acks_recebidos:
            print(f"[TIMEOUT SR] Reenviando pacote {seq}")
            cliente.send(pacotes[seq].encode())
            iniciar_sr_timer(seq)  

def receber_ack():
    global base
    while True:
        try:
            resposta = cliente.recv(1024).decode()
            print(f"[RESPOSTA RECEBIDA]: {resposta}")
            if resposta.startswith("ACK"):
                seq_ack = int(resposta.split()[1])
                with lock:
                    acks_recebidos.add(seq_ack)
                    if modo_operacao == "GBN":
                        if seq_ack >= base:
                            base = seq_ack + 1
                            if base == next_seq:
                                if gbn_timer is not None:
                                    gbn_timer.cancel()
                            else:
                                iniciar_gbn_timer()
                    else:  # SR
                        while base in acks_recebidos:
                            if base in sr_timers:
                                sr_timers[base].cancel()
                                del sr_timers[base]
                            base += 1
        except:
            break

threading.Thread(target=receber_ack, daemon=True).start()

while base < len(pacotes):
    with lock:
        while next_seq < base + janela_tamanho and next_seq < len(pacotes):
            print(f"[PACOTE ENVIADO]: {pacotes[next_seq]}")
            cliente.send(pacotes[next_seq].encode())
            if modo_operacao == "GBN":
                if base == next_seq:  
                    iniciar_gbn_timer()
            else:  
                iniciar_sr_timer(next_seq)
            next_seq += 1
    time.sleep(0.1)  

if modo_operacao == "GBN" and gbn_timer is not None:
    gbn_timer.cancel()
if modo_operacao == "SR":
    for t in sr_timers.values():
        t.cancel()

cliente.send("FIM".encode())
print("[SINAL DE FIM ENVIADO]")

cliente.close()