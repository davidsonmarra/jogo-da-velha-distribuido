import socket
import threading
from game import Game

class TicTacToeServer:
    def __init__(self, host='localhost', port=5001):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        self.game = Game()
        self.players = []
        self.current_player_idx = 0
        print(f"Servidor iniciado em {host}:{port}")

    def handle_client(self, client_socket, player_idx):
        """Gerencia a comunicação com um cliente."""
        symbol = 'X' if player_idx == 0 else 'O'
        
        try:
            while True:
                if player_idx == self.current_player_idx:
                    # Enviar estado atual do jogo
                    client_socket.send(f"Sua vez ({symbol}). Digite a posição (linha coluna): {self.game.get_board_str()}".encode())
                    
                    # Receber jogada
                    try:
                        move = client_socket.recv(1024).decode().strip().split()
                        if len(move) != 2:
                            client_socket.send("Formato inválido. Use: linha coluna".encode())
                            continue
                        
                        row, col = map(int, move)
                        if not self.game.make_move(row, col):
                            client_socket.send("Jogada inválida. Tente novamente.".encode())
                            continue
                        
                        # Notificar ambos os jogadores sobre o estado atual
                        board_str = self.game.get_board_str()
                        for p in self.players:
                            p.send(f"\nTabuleiro atual: {board_str}".encode())
                        
                        # Verificar se há vencedor
                        winner = self.game.check_winner()
                        if winner:
                            for p in self.players:
                                p.send(f"\nJogador {winner} venceu!".encode())
                            self.game.reset()
                            break
                        
                        # Verificar empate
                        if self.game.is_board_full():
                            for p in self.players:
                                p.send("\nEmpate!".encode())
                            self.game.reset()
                            break
                        
                        # Próximo jogador
                        self.current_player_idx = 1 - self.current_player_idx
                        
                    except ValueError:
                        client_socket.send("Entrada inválida. Use números para linha e coluna.".encode())
                else:
                    client_socket.send(f"Aguarde sua vez... {self.game.get_board_str()}".encode())
                    threading.Event().wait(1)  # Espera 1 segundo antes de verificar novamente
                    
        except (ConnectionResetError, BrokenPipeError):
            print(f"Jogador {player_idx + 1} desconectou")
        finally:
            if client_socket in self.players:
                self.players.remove(client_socket)
            client_socket.close()

    def start(self):
        """Inicia o servidor e aguarda conexões."""
        try:
            while True:
                print("Aguardando jogadores...")
                while len(self.players) < 2:
                    client_socket, addr = self.server.accept()
                    player_idx = len(self.players)
                    self.players.append(client_socket)
                    print(f"Jogador {player_idx + 1} conectado de {addr}")
                    
                    # Informar ao jogador que ele está conectado
                    client_socket.send(f"Você é o jogador {player_idx + 1} ({'X' if player_idx == 0 else 'O'})".encode())
                    
                    # Iniciar thread para gerenciar o cliente
                    threading.Thread(target=self.handle_client, args=(client_socket, player_idx)).start()
                
                # Aguardar até que um jogador desconecte para aceitar novo jogador
                while len(self.players) == 2:
                    threading.Event().wait(1)
                
                # Resetar o jogo quando um jogador desconectar
                self.game.reset()
                self.current_player_idx = 0
                
        except KeyboardInterrupt:
            print("\nServidor encerrado")
        finally:
            for player in self.players:
                player.close()
            self.server.close()

if __name__ == "__main__":
    server = TicTacToeServer()
    server.start() 