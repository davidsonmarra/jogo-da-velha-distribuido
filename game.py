import random
from typing import Dict, List, Optional
import threading

class Game:
    def __init__(self):
        self.teams = {'A': [], 'B': []}  # Jogadores de cada time
        self.players = {}  # Dicionário com informações dos jogadores
        self.current_drawer = None  # Jogador atual desenhando
        self.current_word = None  # Palavra atual
        self.current_team = 'A'  # Time atual
        self.scores = {'A': 0, 'B': 0}  # Pontuação dos times
        self.host = None  # Host da sala
        self.game_started = False
        self.drawer_lock = threading.Lock()  # Lock para exclusão mútua
        self.words = [
            "cachorro", "gato", "elefante", "girafa", "leão",
            "carro", "avião", "barco", "trem", "bicicleta",
            "casa", "prédio", "escola", "igreja", "hospital",
            "árvore", "flor", "sol", "lua", "estrela",
            "pizza", "hambúrguer", "sorvete", "bolo", "chocolate"
        ]
        self.used_words = set()

    def add_player(self, player_id: str, name: str) -> None:
        """Adiciona um novo jogador ao jogo."""
        self.players[player_id] = {
            'name': name,
            'team': None,
            'score': 0,
            'is_connected': True
        }
        if not self.host:
            self.host = player_id

    def remove_player(self, player_id: str) -> None:
        """Remove um jogador do jogo."""
        if player_id in self.players:
            team = self.players[player_id]['team']
            if team:
                self.teams[team].remove(player_id)
            del self.players[player_id]
            
            # Se era o desenhista, elege um novo
            if player_id == self.current_drawer:
                self.elect_new_drawer()
            
            # Se era o host, elege um novo
            if player_id == self.host:
                self.elect_new_host()

    def start_game(self) -> bool:
        """Inicia o jogo, dividindo os times aleatoriamente."""
        if len(self.players) < 2:
            return False

        # Reseta os times
        self.teams = {'A': [], 'B': []}
        player_ids = list(self.players.keys())
        random.shuffle(player_ids)

        # Divide os jogadores em dois times
        mid = len(player_ids) // 2
        for i, player_id in enumerate(player_ids):
            team = 'A' if i < mid else 'B'
            self.teams[team].append(player_id)
            self.players[player_id]['team'] = team

        self.game_started = True
        self.current_team = 'A'
        self.elect_new_drawer()
        return True

    def elect_new_drawer(self) -> Optional[str]:
        """Elege um novo desenhista usando exclusão mútua."""
        with self.drawer_lock:
            team_players = self.teams[self.current_team]
            if not team_players:
                return None
            
            self.current_drawer = random.choice(team_players)
            self.current_word = self.get_random_word()
            return self.current_drawer

    def elect_new_host(self) -> Optional[str]:
        """Elege um novo host quando o atual desconecta."""
        connected_players = [pid for pid, p in self.players.items() if p['is_connected']]
        if connected_players:
            self.host = connected_players[0]
            return self.host
        return None

    def get_random_word(self) -> str:
        """Retorna uma palavra aleatória não usada."""
        available_words = list(set(self.words) - self.used_words)
        if not available_words:
            self.used_words.clear()
            available_words = self.words
        
        word = random.choice(available_words)
        self.used_words.add(word)
        return word

    def check_guess(self, player_id: str, guess: str) -> bool:
        """Verifica se um palpite está correto."""
        if not self.current_word or not self.game_started:
            return False

        if self.players[player_id]['team'] == self.current_team:
            return False  # Jogadores do mesmo time não podem adivinhar

        is_correct = guess.lower().strip() == self.current_word.lower()
        if is_correct:
            # Pontua para o time que adivinhou
            guessing_team = 'B' if self.current_team == 'A' else 'A'
            self.scores[guessing_team] += 1
            self.players[player_id]['score'] += 1
            
            # Troca o time atual
            self.current_team = guessing_team
            self.elect_new_drawer()

        return is_correct

    def get_game_state(self) -> Dict:
        """Retorna o estado atual do jogo."""
        return {
            'teams': self.teams,
            'scores': self.scores,
            'current_team': self.current_team,
            'current_drawer': self.current_drawer,
            'players': self.players,
            'host': self.host,
            'game_started': self.game_started
        } 