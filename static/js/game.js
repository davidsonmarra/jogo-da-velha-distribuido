document.addEventListener("DOMContentLoaded", () => {
  // Configuração do Socket.IO com opções de reconexão
  const socket = io({
    transports: ["websocket"],
    upgrade: false,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
  });

  let currentRoom = null;
  let playerSymbol = null;
  let isMyTurn = false;

  // Elementos do DOM
  const menu = document.getElementById("menu");
  const gameSection = document.getElementById("gameSection");
  const board = document.getElementById("board");
  const cells = document.querySelectorAll(".cell");
  const createGameBtn = document.getElementById("createGame");
  const joinGameBtn = document.getElementById("joinGame");
  const gameCodeInput = document.getElementById("gameCode");
  const roomCodeDisplay = document.getElementById("roomCode");
  const playerInfoDisplay = document.getElementById("playerInfo");
  const gameStatusDisplay = document.getElementById("gameStatus");
  const newGameBtn = document.getElementById("newGame");

  // Monitoramento do estado da conexão
  socket.on("connect", () => {
    console.log("Conectado ao servidor");
    gameStatusDisplay.textContent = "";
  });

  socket.on("disconnect", () => {
    console.log("Desconectado do servidor");
    gameStatusDisplay.textContent = "Conexão perdida. Tentando reconectar...";
  });

  socket.on("connect_error", (error) => {
    console.log("Erro de conexão:", error);
    gameStatusDisplay.textContent = "Erro de conexão. Tentando reconectar...";
  });

  // Eventos dos botões
  createGameBtn.addEventListener("click", () => {
    if (socket.connected) {
      socket.emit("create_game");
      gameStatusDisplay.textContent = "Criando jogo...";
    } else {
      gameStatusDisplay.textContent = "Erro: Não conectado ao servidor";
    }
  });

  joinGameBtn.addEventListener("click", () => {
    const code = gameCodeInput.value.trim().toUpperCase();
    if (code) {
      if (socket.connected) {
        socket.emit("join_game", { room: code });
        gameStatusDisplay.textContent = "Entrando no jogo...";
      } else {
        gameStatusDisplay.textContent = "Erro: Não conectado ao servidor";
      }
    }
  });

  newGameBtn.addEventListener("click", () => {
    menu.classList.remove("hidden");
    gameSection.classList.add("hidden");
    resetBoard();
  });

  // Eventos do tabuleiro
  cells.forEach((cell) => {
    cell.addEventListener("click", () => {
      if (isMyTurn && cell.textContent === "") {
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);
        socket.emit("make_move", {
          room: currentRoom,
          row: row,
          col: col,
        });
      }
    });
  });

  // Eventos do Socket.IO
  socket.on("game_created", (data) => {
    currentRoom = data.room;
    showGame();
    roomCodeDisplay.textContent = `Código da sala: ${currentRoom}`;
    playerInfoDisplay.textContent = "Aguardando outro jogador...";
    gameStatusDisplay.textContent = "";
  });

  socket.on("game_start", (data) => {
    updateBoard(data.board);
    gameStatusDisplay.textContent = "";
  });

  socket.on("your_turn", (data) => {
    playerSymbol = data.symbol;
    isMyTurn = true;
    playerInfoDisplay.textContent = `Você é ${playerSymbol} - Sua vez!`;
    gameStatusDisplay.textContent = "";
  });

  socket.on("wait_turn", (data) => {
    playerSymbol = data.symbol;
    isMyTurn = false;
    playerInfoDisplay.textContent = `Você é ${playerSymbol} - Aguarde sua vez...`;
    gameStatusDisplay.textContent = "";
  });

  socket.on("board_update", (data) => {
    updateBoard(data.board);
  });

  socket.on("game_over", (data) => {
    isMyTurn = false;
    if (data.winner === "empate") {
      gameStatusDisplay.textContent = "Jogo empatado!";
    } else {
      gameStatusDisplay.textContent = `Jogador ${data.winner} venceu!`;
    }
    newGameBtn.classList.remove("hidden");
  });

  socket.on("error", (data) => {
    console.error("Erro recebido:", data);
    gameStatusDisplay.textContent = `Erro: ${data.message}`;
  });

  socket.on("player_disconnected", () => {
    gameStatusDisplay.textContent = "O outro jogador desconectou!";
    newGameBtn.classList.remove("hidden");
  });

  // Funções auxiliares
  function showGame() {
    menu.classList.add("hidden");
    gameSection.classList.remove("hidden");
    newGameBtn.classList.add("hidden");
  }

  function updateBoard(boardData) {
    cells.forEach((cell, index) => {
      const row = Math.floor(index / 3);
      const col = index % 3;
      cell.textContent = boardData[row][col];
      cell.className = "cell";
      if (boardData[row][col] === "X") {
        cell.classList.add("x");
      } else if (boardData[row][col] === "O") {
        cell.classList.add("o");
      }
    });
  }

  function resetBoard() {
    cells.forEach((cell) => {
      cell.textContent = "";
      cell.className = "cell";
    });
    currentRoom = null;
    playerSymbol = null;
    isMyTurn = false;
    gameStatusDisplay.textContent = "";
    playerInfoDisplay.textContent = "";
    roomCodeDisplay.textContent = "";
  }
});
