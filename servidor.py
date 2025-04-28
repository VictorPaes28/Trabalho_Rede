import socket
import threading

def calcular_checksum(dados):
    return str(sum(bytearray(dados.encode())) % 256)

servidor = socket.socket()
servidor.bind(("localhost", 12345))
servidor.listen(1)

print("Servidor esperando conexão...\n")

conexao, endereco = servidor.accept()
print("Cliente conectado:", endereco)

handshake = conexao.recv(1024).decode()
print("[HANDSHAKE RECEBIDO]:", handshake)

modo_operacao = conexao.recv(1024).decode()
print(f"[MODO OPERACAO RECEBIDO]: {modo_operacao}")

mensagem_completa = {}
esperado = 0

def processar_pacote(pacote):
    global esperado
    try:
        if not pacote or "|" not in pacote:
            return  
        seq, dados, checksum = pacote.split("|")
        seq = int(seq)
        checksum_calculado = calcular_checksum(dados)

        print(f"[PACOTE RECEBIDO]: Seq={seq} Dados={dados} Checksum={checksum_calculado}")

        if checksum_calculado == checksum:
            if modo_operacao == "GBN":
                if seq == esperado:
                    mensagem_completa[seq] = dados
                    esperado += 1
                ack = f"ACK {esperado-1}"
                conexao.send(ack.encode())
                print(f"[ACK ENVIADO]: {ack}")
            else:  
                mensagem_completa[seq] = dados
                ack = f"ACK {seq}"
                conexao.send(ack.encode())
                print(f"[ACK ENVIADO]: {ack}")
        else:
            nack = f"NACK {seq}"
            conexao.send(nack.encode())
            print(f"[NACK ENVIADO]: {nack}")
    except:
        print("[ERRO] Pacote mal formatado")

while True:
    pacote = conexao.recv(1024).decode()
    if pacote == "FIM":
        print("[FIM da transmissão recebido]")
        break
    threading.Thread(target=processar_pacote, args=(pacote,)).start()

mensagem_final = ""
for seq in sorted(mensagem_completa):
    mensagem_final += mensagem_completa[seq]

print("\n[MENSAGEM FINAL RECEBIDA COMPLETA]:", mensagem_final)

conexao.close()
servidor.close()
