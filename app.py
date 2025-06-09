from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from game import Game
import json
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'jogo-da-velha-secret!')
socketio = SocketIO(app,
                   cors_allowed_origins="*",
                   async_mode='gevent',
                   logger=True,
                   engineio_logger=True,
                   ping_timeout=60)

# Dicionário para armazenar os jogos ativos
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Manipula nova conexão."""
    logger.info(f'Cliente conectado: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Limpa o jogo quando um jogador desconecta."""
    logger.info(f'Cliente desconectado: {request.sid}')
    for room in list(games.keys()):
        if request.sid in games[room]['players']:
            emit('player_disconnected', to=room)
            logger.info(f'Removendo jogo da sala: {room}')
            del games[room]
            break

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
    logger.info(f'Novo jogo criado na sala: {room}')
    emit('game_created', {'room': room})

@socketio.on('join_game')
def on_join_game(data):
    """Permite que um jogador entre em um jogo existente."""
    room = data['room']
    logger.info(f'Tentativa de entrar na sala: {room}')
    
    if room not in games:
        logger.warning(f'Sala não encontrada: {room}')
        emit('error', {'message': 'Sala não encontrada'})
        return
        
    if len(games[room]['players']) >= 2:
        logger.warning(f'Sala cheia: {room}')
        emit('error', {'message': 'Sala cheia'})
        return
        
    join_room(room)
    games[room]['players'].append(request.sid)
    logger.info(f'Jogador {request.sid} entrou na sala: {room}')
    
    # Se este for o segundo jogador, o jogo pode começar
    if len(games[room]['players']) == 2:
        logger.info(f'Jogo iniciando na sala: {room}')
        emit('game_start', {'board': games[room]['game'].board}, to=room)
        emit('your_turn', {'symbol': 'X'}, to=games[room]['players'][0])
        emit('wait_turn', {'symbol': 'O'}, to=games[room]['players'][1])

@socketio.on('make_move')
def on_make_move(data):
    """Processa uma jogada de um jogador."""
    room = data['room']
    row = data['row']
    col = data['col']
    
    if room not in games:
        logger.warning(f'Tentativa de jogada em sala inexistente: {room}')
        emit('error', {'message': 'Jogo não encontrado'})
        return
        
    game = games[room]['game']
    players = games[room]['players']
    
    # Verifica se é a vez do jogador
    player_idx = players.index(request.sid) if request.sid in players else -1
    if player_idx != games[room]['current_player']:
        logger.warning(f'Jogada fora de turno na sala {room}')
        emit('error', {'message': 'Não é sua vez'})
        return
    
    # Tenta fazer a jogada
    if game.make_move(row, col):
        # Envia o novo estado do tabuleiro para todos
        emit('board_update', {'board': game.board}, to=room)
        
        # Verifica se há um vencedor
        winner = game.check_winner()
        if winner:
            logger.info(f'Jogo finalizado na sala {room}. Vencedor: {winner}')
            emit('game_over', {'winner': winner}, to=room)
            del games[room]
            return
            
        # Verifica se houve empate
        if game.is_board_full():
            logger.info(f'Jogo empatado na sala {room}')
            emit('game_over', {'winner': 'empate'}, to=room)
            del games[room]
            return
            
        # Próximo jogador
        games[room]['current_player'] = 1 - games[room]['current_player']
        next_player = games[room]['players'][games[room]['current_player']]
        emit('your_turn', room=next_player)
        emit('wait_turn', room=players[1 - games[room]['current_player']])
    else:
        logger.warning(f'Jogada inválida na sala {room}: ({row}, {col})')
        emit('error', {'message': 'Jogada inválida'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app,
                host='0.0.0.0',
                port=port,
                allow_unsafe_werkzeug=True,
                debug=False) 