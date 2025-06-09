class Game:
    def __init__(self):
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        
    def make_move(self, row, col):
        """Realiza uma jogada no tabuleiro."""
        if 0 <= row <= 2 and 0 <= col <= 2 and self.board[row][col] == ' ':
            self.board[row][col] = self.current_player
            self.current_player = 'O' if self.current_player == 'X' else 'X'
            return True
        return False
    
    def check_winner(self):
        """Verifica se há um vencedor."""
        # Verificar linhas
        for row in self.board:
            if row[0] == row[1] == row[2] != ' ':
                return row[0]
        
        # Verificar colunas
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != ' ':
                return self.board[0][col]
        
        # Verificar diagonais
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return self.board[0][2]
        
        return None
    
    def is_board_full(self):
        """Verifica se o tabuleiro está cheio (empate)."""
        return all(all(cell != ' ' for cell in row) for row in self.board)
    
    def get_board_str(self):
        """Retorna uma representação string do tabuleiro."""
        board_str = "\n"
        for i, row in enumerate(self.board):
            board_str += f" {row[0]} | {row[1]} | {row[2]} \n"
            if i < 2:
                board_str += "---+---+---\n"
        return board_str
    
    def reset(self):
        """Reinicia o jogo."""
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X' 