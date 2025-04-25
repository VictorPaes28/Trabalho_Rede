import socket

cliente = socket.socket()
cliente.connect(("localhost", 12345))

modo = "lote"
tamanho = "3"
handshake = f"modo:{modo},tamanho:{tamanho}"
cliente.send(handshake.encode())
print(f"[HANDSHAKE ENVIADO]: {handshake}")

mensagem = input("Digite a mensagem para enviar ao servidor: ")
tamanho_pacote = 3

for i in range(0, len(mensagem), tamanho_pacote):
    dados = mensagem[i:i+tamanho_pacote]
    seq = i // tamanho_pacote
    pacote = f"{seq}|{dados}"

    cliente.send(pacote.encode())
    print(f"[PACOTE ENVIADO]: {pacote}")

    ack = cliente.recv(1024).decode()
    print(f"[ACK RECEBIDO PELO CLIENTE]: {ack}\n")

cliente.send("FIM".encode())
print("[SINAL DE FIM ENVIADO]")

cliente.close()
