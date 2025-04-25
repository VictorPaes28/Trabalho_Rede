import socket

servidor = socket.socket()
servidor.bind(("localhost", 12345))
servidor.listen(1)

print("Servidor esperando conexão...\n")

conexao, endereco = servidor.accept()
print("Cliente conectado:", endereco)

handshake = conexao.recv(1024).decode()
print("[HANDSHAKE RECEBIDO]:", handshake)

mensagem_completa = ""
while True:
    pacote = conexao.recv(1024).decode()
    if pacote == "FIM":
        print("[FIM da transmissão recebido]")
        break

    print(f"[PACOTE RECEBIDO]: {pacote}")
    try:
        seq, dados = pacote.split("|")
        print(f"[META] Seq: {seq} | Dados: {dados}")
        mensagem_completa += dados

        ack = f"ACK {seq}"
        conexao.send(ack.encode())
        print(f"[ACK ENVIADO]: {ack}\n")
    except ValueError:
        print("[ERRO] Formato inválido do pacote.")

print("\n[MENSAGEM FINAL RECEBIDA COMPLETA]:", mensagem_completa)

conexao.close()
servidor.close()
