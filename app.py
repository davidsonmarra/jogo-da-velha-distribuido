from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from game import Game
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dicionário para armazenar os jogos ativos
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_game')
def on_create_game(data):
    """Cria uma nova sala de jogo."""
    try:
        room = generate_room_code()
        games[room] = Game()
        join_room(room)
        
        # Adiciona o jogador como host
        player_name = data.get('player_name', f'Jogador_{len(games[room].players) + 1}')
        games[room].add_player(request.sid, player_name)
        
        emit('game_created', {
            'room': room,
            'is_host': True,
            'player_id': request.sid
        })
        logger.info(f'Jogo criado na sala: {room}')
    except Exception as e:
        logger.error(f'Erro ao criar jogo: {str(e)}')
        emit('error', {'message': 'Erro ao criar jogo'})

@socketio.on('join_game')
def on_join_game(data):
    """Permite um jogador entrar em uma sala existente."""
    try:
        room = data['room'].upper()
        if room not in games:
            emit('error', {'message': 'Sala não encontrada'})
            return

        game = games[room]
        if len(game.players) >= 10:
            emit('error', {'message': 'Sala cheia'})
            return

        join_room(room)
        player_name = data.get('player_name', f'Jogador_{len(game.players) + 1}')
        game.add_player(request.sid, player_name)

        emit('game_joined', {
            'room': room,
            'is_host': request.sid == game.host,
            'player_id': request.sid
        })
        
        # Notifica todos na sala sobre o novo jogador
        emit('player_joined', {
            'game_state': game.get_game_state()
        }, room=room)
        
        logger.info(f'Jogador {player_name} entrou na sala: {room}')
    except Exception as e:
        logger.error(f'Erro ao entrar no jogo: {str(e)}')
        emit('error', {'message': 'Erro ao entrar no jogo'})

@socketio.on('start_game')
def on_start_game(data):
    """Inicia o jogo quando o host decide começar."""
    try:
        room = data['room']
        game = games.get(room)
        
        if not game or request.sid != game.host:
            emit('error', {'message': 'Apenas o host pode iniciar o jogo'})
            return

        if game.start_game():
            game_state = game.get_game_state()
            logger.info(f'Jogo iniciado na sala: {room} com estado: {game_state}')
            
            # Envia o estado do jogo para todos
            emit('game_started', {
                'game_state': game_state
            }, room=room)
            
            # Envia a palavra apenas para o desenhista
            if game.current_drawer and game.current_word:
                logger.info(f'Enviando palavra "{game.current_word}" para o desenhista {game.current_drawer}')
                emit('word_to_draw', {
                    'word': game.current_word
                }, to=game.current_drawer)
        else:
            emit('error', {'message': 'Não há jogadores suficientes'})
    except Exception as e:
        logger.error(f'Erro ao iniciar jogo: {str(e)}')
        emit('error', {'message': 'Erro ao iniciar jogo'})

@socketio.on('draw')
def on_draw(data):
    """Recebe e transmite os dados do desenho."""
    try:
        room = data['room']
        game = games.get(room)
        
        if not game:
            logger.warning(f'Tentativa de desenho em sala inexistente: {room}')
            return
            
        if request.sid != game.current_drawer:
            logger.warning(f'Tentativa de desenho por jogador não autorizado: {request.sid}')
            return

        logger.debug(f'Desenhando na sala {room}: {data}')
        
        # Transmite o desenho para todos na sala
        emit('draw_data', {
            'points': data['points'],
            'color': data['color'],
            'thickness': data['thickness']
        }, broadcast=True, room=room)
        
    except Exception as e:
        logger.error(f'Erro ao processar desenho: {str(e)}')

@socketio.on('clear_canvas')
def on_clear_canvas(data):
    """Limpa o canvas para todos os jogadores na sala."""
    try:
        room = data['room']
        game = games.get(room)
        
        if not game or request.sid != game.current_drawer:
            return

        # Transmite o comando de limpar para todos na sala
        emit('clear_canvas', broadcast=True, room=room)
        logger.info(f'Canvas limpo na sala: {room}')
    except Exception as e:
        logger.error(f'Erro ao limpar canvas: {str(e)}')

@socketio.on('guess')
def on_guess(data):
    """Processa tentativas de adivinhar a palavra."""
    try:
        room = data['room']
        guess = data['guess']
        game = games.get(room)

        if not game:
            return

        if game.check_guess(request.sid, guess):
            emit('correct_guess', {
                'game_state': game.get_game_state(),
                'player_id': request.sid
            }, room=room)
            logger.info(f'Palavra correta adivinhada na sala: {room}')
    except Exception as e:
        logger.error(f'Erro ao processar palpite: {str(e)}')

@socketio.on('disconnect')
def on_disconnect():
    """Gerencia a desconexão de jogadores."""
    try:
        for room, game in games.items():
            if request.sid in game.players:
                game.remove_player(request.sid)
                leave_room(room)
                
                if len(game.players) == 0:
                    del games[room]
                    logger.info(f'Sala removida: {room}')
                else:
                    emit('player_disconnected', {
                        'game_state': game.get_game_state()
                    }, room=room)
                    logger.info(f'Jogador desconectado da sala: {room}')
                break
    except Exception as e:
        logger.error(f'Erro ao desconectar jogador: {str(e)}')

def generate_room_code(length=4):
    """Gera um código único para a sala."""
    import random
    import string
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=length))
        if code not in games:
            return code

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True) 