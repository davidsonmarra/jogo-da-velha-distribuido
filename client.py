import socket
import sys

class TicTacToeClient:
    def __init__(self, host='localhost', port=5000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((host, port))
            print("Conectado ao servidor!")
        except ConnectionRefusedError:
            print("Não foi possível conectar ao servidor. Verifique se ele está rodando.")
            sys.exit(1)

    def start(self):
        """Inicia o cliente e gerencia a comunicação com o servidor."""
        try:
            while True:
                # Receber mensagem do servidor
                response = self.client.recv(1024).decode()
                if not response:
                    print("\nConexão com o servidor perdida.")
                    break
                
                print(response)
                
                if "venceu" in response or "Empate" in response:
                    print("\nFim do jogo!")
                    break
                
                if "Sua vez" in response:
                    while True:
                        try:
                            move = input("Digite sua jogada (linha coluna): ")
                            # Validar formato da entrada
                            row, col = map(int, move.split())
                            if 0 <= row <= 2 and 0 <= col <= 2:
                                self.client.send(move.encode())
                                break
                            else:
                                print("Posição inválida. Use números entre 0 e 2.")
                        except ValueError:
                            print("Entrada inválida. Use o formato: linha coluna (ex: 0 1)")
                
        except KeyboardInterrupt:
            print("\nJogo encerrado pelo usuário")
        except ConnectionResetError:
            print("\nConexão com o servidor perdida")
        finally:
            self.client.close()

if __name__ == "__main__":
    client = TicTacToeClient()
    client.start() 