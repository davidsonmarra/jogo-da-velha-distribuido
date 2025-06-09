from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from game import Game
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jogo-da-velha-secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Dicionário para armazenar os jogos ativos
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_game')
def on_create_game():
    """Cria um novo jogo e retorna o código da sala."""
    import random
    import string
    
    # Gera um código aleatório para a sala
    room = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    games[room] = {
        'game': Game(),
        'players': [],
        'current_player': 0
    }
    join_room(room)
    games[room]['players'].append(request.sid)
    emit('game_created', {'room': room})

@socketio.on('join_game')
def on_join_game(data):
    """Permite que um jogador entre em um jogo existente."""
    room = data['room']
    if room in games and len(games[room]['players']) < 2:
        join_room(room)
        games[room]['players'].append(request.sid)
        
        # Se este for o segundo jogador, o jogo pode começar
        if len(games[room]['players']) == 2:
            emit('game_start', {'board': games[room]['game'].board}, to=room)
            emit('your_turn', {'symbol': 'X'}, to=games[room]['players'][0])
            emit('wait_turn', {'symbol': 'O'}, to=games[room]['players'][1])
    else:
        emit('error', {'message': 'Sala não encontrada ou cheia'})

@socketio.on('make_move')
def on_make_move(data):
    """Processa uma jogada de um jogador."""
    room = data['room']
    row = data['row']
    col = data['col']
    
    if room not in games:
        emit('error', {'message': 'Jogo não encontrado'})
        return
        
    game = games[room]['game']
    players = games[room]['players']
    
    # Verifica se é a vez do jogador
    player_idx = players.index(request.sid) if request.sid in players else -1
    if player_idx != games[room]['current_player']:
        emit('error', {'message': 'Não é sua vez'})
        return
    
    # Tenta fazer a jogada
    if game.make_move(row, col):
        # Envia o novo estado do tabuleiro para todos
        emit('board_update', {'board': game.board}, to=room)
        
        # Verifica se há um vencedor
        winner = game.check_winner()
        if winner:
            emit('game_over', {'winner': winner}, to=room)
            del games[room]
            return
            
        # Verifica se houve empate
        if game.is_board_full():
            emit('game_over', {'winner': 'empate'}, to=room)
            del games[room]
            return
            
        # Próximo jogador
        games[room]['current_player'] = 1 - games[room]['current_player']
        next_player = games[room]['players'][games[room]['current_player']]
        emit('your_turn', room=next_player)
        emit('wait_turn', room=players[1 - games[room]['current_player']])
    else:
        emit('error', {'message': 'Jogada inválida'})

@socketio.on('disconnect')
def on_disconnect():
    """Limpa o jogo quando um jogador desconecta."""
    for room in list(games.keys()):
        if request.sid in games[room]['players']:
            emit('player_disconnected', to=room)
            del games[room]
            break

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app, host='0.0.0.0', port=port) 