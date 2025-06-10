# Imagem & Ação Online

Um jogo multiplayer de desenho e adivinhação inspirado no clássico Imagem & Ação, implementado com Python, Flask e WebSocket.

## Características

- Suporte para múltiplos jogadores (até 10 por sala)
- Sistema de times (A e B)
- Desenho em tempo real
- Sistema de pontuação
- Interface responsiva
- Controles de desenho (cor e espessura)
- Eleição automática de novo desenhista
- Tratamento de desconexões

## Requisitos

- Python 3.8+
- Flask
- Flask-SocketIO
- Flask-CORS
- Eventlet

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/imagem-e-acao.git
cd imagem-e-acao
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Executando o Jogo

1. Inicie o servidor:

```bash
python app.py
```

2. Abra o navegador e acesse:

```
http://localhost:5001
```

## Como Jogar

1. O primeiro jogador cria uma sala e recebe um código
2. Outros jogadores podem entrar usando o código da sala
3. Quando houver pelo menos 2 jogadores, o host pode iniciar o jogo
4. Os jogadores são divididos aleatoriamente em dois times
5. Um jogador do time A é escolhido para desenhar
6. O time B tenta adivinhar o que está sendo desenhado
7. Se acertarem, ganham pontos e a vez passa para o time B desenhar
8. O jogo continua alternando entre os times

## Tecnologias Utilizadas

- Backend:

  - Python
  - Flask
  - Flask-SocketIO
  - Flask-CORS
  - Eventlet

- Frontend:
  - HTML5 Canvas
  - JavaScript
  - Socket.IO Client
  - Bootstrap

## Contribuindo

Sinta-se à vontade para abrir issues ou enviar pull requests com melhorias.

## Licença

Este projeto está licenciado sob a MIT License.
