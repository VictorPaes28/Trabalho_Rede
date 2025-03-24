import socket

cliente = socket.socket()
cliente.connect(("localhost", 12345))

modo = "lote"
tamanho = "3"
mensagem = f"modo:{modo},tamanho:{tamanho}"

cliente.send(mensagem.encode())
resposta = cliente.recv(1024).decode()

print("Resposta do servidor:", resposta)

cliente.close()