import socket

servidor = socket.socket()
servidor.bind(("localhost", 12345))
servidor.listen(1)

print("Servidor esperando conexão...")

conexao, endereco = servidor.accept()
print("Cliente conectado:", endereco)

mensagem = conexao.recv(1024).decode()
print("Mensagem recebida do cliente:", mensagem)

resposta = "Servidor recebeu o modo e tamanho"
conexao.send(resposta.encode())

conexao.close()
servidor.close()
