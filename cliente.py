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
                        if seq_ack == base:
                            base += 1
                    else:
                        while base in acks_recebidos:
                            base += 1
        except:
            break

threading.Thread(target=receber_ack, daemon=True).start()

while base < len(pacotes):
    with lock:
        while next_seq < base + janela_tamanho and next_seq < len(pacotes):
            print(f"[PACOTE ENVIADO]: {pacotes[next_seq]}")
            cliente.send(pacotes[next_seq].encode())
            next_seq += 1

    time.sleep(timeout)

    with lock:
        if modo_operacao == "GBN":
            if base < next_seq:
                print("[TIMEOUT] Reenviando pacotes Go-Back-N a partir do base")
                for i in range(base, next_seq):
                    print(f"[REENVIANDO]: {pacotes[i]}")
                    cliente.send(pacotes[i].encode())
        else:
            for i in range(base, next_seq):
                if i not in acks_recebidos:
                    print(f"[REENVIANDO]: {pacotes[i]}")
                    cliente.send(pacotes[i].encode())

cliente.send("FIM".encode())
print("[SINAL DE FIM ENVIADO]")

cliente.close()