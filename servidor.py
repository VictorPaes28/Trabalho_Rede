import socket
import threading

def calcular_checksum(dados):
    return str(sum(ord(c) for c in dados) % 256)

HOST = "localhost"
PORT = 12345

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORT))
servidor.listen(1)

print("Servidor aguardando conexão...")

conn, addr = servidor.accept()
print(f"Conectado a {addr}")

handshake = conn.recv(1024).decode()
print(f"[HANDSHAKE RECEBIDO]: {handshake}")

modo = conn.recv(1024).decode()
print(f"[MODO RECEBIDO]: {modo}")

esperado = 0
pacotes_recebidos = {}

def tratar_pacote(pacote):
    global esperado
    if not pacote or "|" not in pacote:
        return

    partes = pacote.strip().split("|")
    if len(partes) != 3:
        print("[ERRO] Pacote mal formado")
        return

    seq, dados, checksum = partes
    seq = int(seq)
    checksum = int(checksum)

    checksum_calc = sum(ord(c) for c in dados) % 256

    print(f"[PACOTE RECEBIDO]: Seq={seq} Dados={dados} Checksum={checksum_calc}")

    if checksum != checksum_calc:
        print(f"[ERRO] Checksum incorreto para pacote {seq}")
        return

    if modo == "gbn":
        if seq == esperado:
            pacotes_recebidos[seq] = dados
            esperado += 1
            ack = f"ACK {seq}"
        else:
            ack = f"ACK {esperado-1}"
        conn.send(ack.encode())
        print(f"[ACK ENVIADO]: {ack}")
    else:  
        pacotes_recebidos[seq] = dados
        ack = f"ACK {seq}"
        conn.send(ack.encode())
        print(f"[ACK ENVIADO]: {ack}")

while True:
    pacote = conn.recv(1024).decode()
    if pacote == "FIM":
        print("[FIM recebido]")
        break
    threading.Thread(target=tratar_pacote, args=(pacote,)).start()

mensagem = "".join(pacotes_recebidos[i] for i in sorted(pacotes_recebidos))
print(f"[MENSAGEM FINAL]: {mensagem}")

conn.close()
servidor.close()
