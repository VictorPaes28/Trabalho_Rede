import socket

HOST = "localhost"
PORT = 5065

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

try:
    perder_pacote = int(input(" So execute o cliente após digitar o número do pacote a ser perdido (-1 para nenhum): "))
except ValueError:
    perder_pacote = -1

print("[SERVIDOR] Aguardando conexão... (So execute o cliente após esta mensagem)")
try:
    conn, _ = server.accept()
except Exception as e:
    print(f"[SERVIDOR] Erro ao aceitar conexão: {e}")
    server.close()
    exit(1)

def checksum(payload):
    return sum(ord(c) for c in payload)

buffer = ""
while "\n" not in buffer:
    try:
        buffer += conn.recv(1024).decode()
    except (ConnectionResetError, BrokenPipeError):
        print("[SERVIDOR] Erro ao receber handshake: cliente desconectou.")
        conn.close()
        server.close()
        exit(1)

try:
    modo, max_len, window = buffer.strip().split(";")
    max_len = int(max_len)
    window_size = int(window)
except Exception as e:
    print(f"[SERVIDOR] Erro ao processar handshake: {e}")
    conn.close()
    server.close()
    exit(1)

try:
    conn.send("HANDSHAKE_OK\n".encode())
except (ConnectionResetError, BrokenPipeError):
    print("[SERVIDOR] Erro ao enviar HANDSHAKE_OK: cliente desconectou.")
    conn.close()
    server.close()
    exit(1)

print(f"[SERVIDOR] Handshake: modo={modo}, max_payload={max_len}, janela={window_size}\n")

expected_seq = 0
received = {}

while True:
    try:
        data = conn.recv(1024).decode()
        if not data:
            break
    except (ConnectionResetError, BrokenPipeError):
        print("[SERVIDOR] Cliente desconectou de forma inesperada.")
        break

    lines = data.strip().split("\n")
    for line in lines:
        try:
            parts = {p.split('=')[0]: p.split('=')[1] for p in line.split('|')}
            seq = int(parts["seq"])
            payload = parts["data"]
            sum_recv = int(parts["sum"].replace('&', ''))
        except Exception:
            print(f"[SERVIDOR] Pacote mal formado ou erro de parsing: {line}")
            continue

        if seq == perder_pacote:
            print(f"[SERVIDOR] Simulação: pacote {seq} perdido\n")
            perder_pacote = -1
            continue

        if checksum(payload) != sum_recv:
            print(f"[SERVIDOR] Checksum inválido para seq={seq}. Esperado: {checksum(payload)}, Recebido: {sum_recv}")
            try:
                conn.send(f"NACK|{seq}\n".encode())
            except (ConnectionResetError, BrokenPipeError):
                print("[SERVIDOR] Falha ao enviar NACK: cliente desconectou.")
                conn.close()
                server.close()
                exit(1)
            continue

        if modo == "em_rajada":
            if seq == expected_seq:
                received[seq] = payload
                expected_seq += 1
                while expected_seq in received:
                    expected_seq += 1
                print(f"[SERVIDOR] Pacote {seq} OK (em ordem). ACK cumulativo enviado: {expected_seq}")
                try:
                    conn.send(f"ACK|{expected_seq}\n".encode())
                except (ConnectionResetError, BrokenPipeError):
                    print("[SERVIDOR] Falha ao enviar ACK: cliente desconectou.")
                    conn.close()
                    server.close()
                    exit(1)
            else:
                print(f"[SERVIDOR] Pacote fora de ordem (GBN): seq={seq}, esperado={expected_seq}. Reenviando ACK|{expected_seq}")
                try:
                    conn.send(f"ACK|{expected_seq}\n".encode())
                except (ConnectionResetError, BrokenPipeError):
                    print("[SERVIDOR] Falha ao reenviar ACK: cliente desconectou.")
                    conn.close()
                    server.close()
                    exit(1)
        else:
            if seq not in received:
                print(f"[SERVIDOR] Pacote {seq} armazenado (SR). ACK individual enviado: {seq}")
                received[seq] = payload
            else:
                print(f"[SERVIDOR] Pacote {seq} duplicado (SR). ACK individual reenviado.")
            try:
                conn.send(f"ACK|{seq}\n".encode())
            except (ConnectionResetError, BrokenPipeError):
                print("[SERVIDOR] Falha ao enviar ACK (SR): cliente desconectou.")
                conn.close()
                server.close()
                exit(1)

# Reconstrução robusta da mensagem final
try:
    mensagem_final = ''.join(received[i] for i in sorted(received))
    print(f"\n[SERVIDOR] Mensagem recebida: {mensagem_final}")
except Exception as e:
    print(f"[SERVIDOR] Erro ao reconstruir mensagem final: {e}")
    print(f"[SERVIDOR] Pacotes recebidos: {received}")

try:
    conn.close()
    server.close()
    print("[SERVIDOR] Conexão encerrada.")
except Exception:
    print("[SERVIDOR] Erro ao fechar conexão.")
