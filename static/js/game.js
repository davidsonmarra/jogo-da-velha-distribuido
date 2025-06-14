document.addEventListener("DOMContentLoaded", () => {
  // Configuração do Socket.IO
  const socket = io();
  let isDrawing = false;
  let lastX = 0;
  let lastY = 0;
  let currentColor = "#000000";
  let currentThickness = 5;
  let isHost = false;
  let playerId = null;
  let currentRoom = null;
  let canDraw = false; // Nova variável para controlar permissão de desenho
  let currentGameState = null; // Variável para armazenar o estado atual do jogo
  let isWaitingForWord = false; // Novo flag para controlar solicitações de palavra

  // Elementos do DOM
  const menu = document.getElementById("menu");
  const gameSection = document.getElementById("gameSection");
  const waitingRoom = document.getElementById("waitingRoom");
  const gameArea = document.getElementById("gameArea");
  const canvas = document.getElementById("drawingCanvas");
  const ctx = canvas.getContext("2d");
  const colorPicker = document.getElementById("colorPicker");
  const thicknessPicker = document.getElementById("thicknessPicker");
  const drawingControls = document.getElementById("drawingControls");
  const hostControls = document.getElementById("hostControls");
  const gameControls = document.getElementById("gameControls");
  const gameStatus = document.getElementById("gameStatus");
  const teamAPlayers = document.getElementById("teamAPlayers");
  const teamBPlayers = document.getElementById("teamBPlayers");
  const teamAScore = document.getElementById("teamAScore");
  const teamBScore = document.getElementById("teamBScore");
  const waitingPlayers = document.getElementById("waitingPlayers");
  const copyRoomCode = document.getElementById("copyRoomCode");

  // Configuração do Canvas
  function resizeCanvas() {
    const container = canvas.parentElement;
    const rect = container.getBoundingClientRect();

    // Define as dimensões do canvas
    canvas.width = rect.width || 800; // fallback para 800px
    canvas.height = rect.height || 600; // fallback para 600px

    // Restaura o contexto após redimensionar
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = currentThickness;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    console.log("Canvas redimensionado:", {
      width: canvas.width,
      height: canvas.height,
    });
  }

  // Função para inicializar o canvas
  function initializeCanvas() {
    console.log("Inicializando canvas...");

    // Força o canvas a ser visível
    canvas.style.display = "block";

    // Tenta redimensionar algumas vezes para garantir
    resizeCanvas();

    // Agenda algumas tentativas adicionais
    setTimeout(resizeCanvas, 100);
    setTimeout(resizeCanvas, 500);
    setTimeout(resizeCanvas, 1000);
  }

  // Observer para monitorar mudanças na visibilidade do gameSection
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.target.classList.contains("hidden")) {
        console.log("Game section hidden");
      } else {
        console.log("Game section visible, inicializando canvas...");
        initializeCanvas();
      }
    });
  });

  // Observa mudanças na classe do gameSection
  observer.observe(gameSection, {
    attributes: true,
    attributeFilter: ["class"],
  });

  // Funções de desenho
  function getCanvasPoint(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    if (e.touches) {
      return {
        x: (e.touches[0].clientX - rect.left) * scaleX,
        y: (e.touches[0].clientY - rect.top) * scaleY,
      };
    }

    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  }

  function startDrawing(e) {
    if (!canDraw) {
      console.log("Não tem permissão para desenhar");
      return;
    }

    e.preventDefault();
    isDrawing = true;

    const point = getCanvasPoint(e);
    lastX = point.x;
    lastY = point.y;

    console.log("Iniciando desenho em:", point);
  }

  function draw(e) {
    if (!isDrawing || !canDraw) return;

    e.preventDefault();
    const point = getCanvasPoint(e);

    console.log("Desenhando de", { x: lastX, y: lastY }, "para", point);

    const points = {
      x0: lastX,
      y0: lastY,
      x1: point.x,
      y1: point.y,
    };

    // Desenha localmente
    drawLine(points);

    // Envia para o servidor apenas se for o desenhista
    if (canDraw) {
      socket.emit("draw", {
        room: currentRoom,
        points: points,
        color: currentColor,
        thickness: currentThickness,
      });
    }

    lastX = point.x;
    lastY = point.y;
  }

  function stopDrawing(e) {
    if (e) e.preventDefault();
    isDrawing = false;
  }

  function drawLine(points) {
    ctx.beginPath();
    ctx.moveTo(points.x0, points.y0);
    ctx.lineTo(points.x1, points.y1);
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = currentThickness;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();
  }

  // Eventos de mouse e touch
  canvas.addEventListener("mousedown", startDrawing);
  canvas.addEventListener("mousemove", draw);
  canvas.addEventListener("mouseup", stopDrawing);
  canvas.addEventListener("mouseout", stopDrawing);

  canvas.addEventListener("touchstart", startDrawing, { passive: false });
  canvas.addEventListener("touchmove", draw, { passive: false });
  canvas.addEventListener("touchend", stopDrawing, { passive: false });
  canvas.addEventListener("touchcancel", stopDrawing, { passive: false });

  // Previne o scroll da página enquanto desenha
  canvas.addEventListener(
    "touchmove",
    (e) => {
      if (isDrawing) e.preventDefault();
    },
    { passive: false }
  );

  // Eventos dos Controles de Desenho
  colorPicker.addEventListener("change", (e) => {
    currentColor = e.target.value;
  });

  thicknessPicker.addEventListener("input", (e) => {
    currentThickness = parseInt(e.target.value);
  });

  document.getElementById("clearCanvas").addEventListener("click", () => {
    if (!canDraw) return; // Só permite limpar se for o desenhista atual

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    socket.emit("clear_canvas", { room: currentRoom });
  });

  // Evento para limpar canvas recebido do servidor
  socket.on("clear_canvas", () => {
    console.log("Limpando canvas");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  });

  // Eventos do Menu
  document.getElementById("createGame").addEventListener("click", () => {
    const playerName =
      document.getElementById("playerName").value.trim() || "Jogador";
    socket.emit("create_game", { player_name: playerName });
  });

  document.getElementById("joinGame").addEventListener("click", () => {
    const code = document.getElementById("gameCode").value.trim().toUpperCase();
    const playerName =
      document.getElementById("playerName").value.trim() || "Jogador";
    if (code) {
      socket.emit("join_game", { room: code, player_name: playerName });
    }
  });

  document.getElementById("startGame").addEventListener("click", () => {
    socket.emit("start_game", { room: currentRoom });
  });

  document.getElementById("submitGuess").addEventListener("click", () => {
    const guess = document.getElementById("guessInput").value.trim();
    if (guess) {
      socket.emit("guess", { room: currentRoom, guess: guess });
      document.getElementById("guessInput").value = "";
    }
  });

  // Eventos do Socket
  socket.on("game_created", (data) => {
    currentRoom = data.room;
    isHost = data.is_host;
    playerId = data.player_id;
    document.getElementById("roomCode").textContent = `Sala: ${currentRoom}`;
    menu.classList.add("hidden");
    gameSection.classList.remove("hidden");
    waitingRoom.classList.remove("hidden");
    gameArea.classList.add("hidden");
    if (isHost) {
      hostControls.classList.remove("hidden");
    }
    // Inicializa o canvas quando o jogo é criado
    initializeCanvas();
  });

  socket.on("game_joined", (data) => {
    currentRoom = data.room;
    isHost = data.is_host;
    playerId = data.player_id;
    document.getElementById("roomCode").textContent = `Sala: ${currentRoom}`;
    menu.classList.add("hidden");
    gameSection.classList.remove("hidden");
    waitingRoom.classList.remove("hidden");
    gameArea.classList.add("hidden");
    if (isHost) {
      hostControls.classList.remove("hidden");
    }
    // Inicializa o canvas quando entra no jogo
    initializeCanvas();
  });

  socket.on("player_joined", (data) => {
    updateWaitingRoom(data.game_state);
  });

  function requestWord() {
    if (isWaitingForWord) {
      console.log(
        "Já estamos aguardando uma palavra, ignorando nova solicitação"
      );
      return;
    }

    console.log("Solicitando palavra do servidor...");
    isWaitingForWord = true;
    socket.emit("request_word", { room: currentRoom });

    // Feedback visual imediato
    gameStatus.textContent = "Aguardando a palavra para desenhar...";
    gameStatus.classList.remove("hidden");
  }

  socket.on("game_started", (data) => {
    console.log("Jogo iniciado", data);
    waitingRoom.classList.add("hidden");
    gameArea.classList.remove("hidden");
    updateGameState(data.game_state);
    hostControls.classList.add("hidden");
    initializeCanvas();

    // Se for o primeiro desenhista, solicita a palavra
    if (data.game_state.current_drawer === playerId) {
      console.log("Sou o primeiro desenhista, solicitando palavra...");
      requestWord();
    } else {
      gameStatus.textContent = "Aguardando o primeiro desenho...";
      gameStatus.classList.remove("hidden");
    }
  });

  socket.on("word_to_draw", (data) => {
    console.log("Recebendo palavra para desenhar", {
      word: data.word,
      current_drawer: currentGameState?.current_drawer,
      meu_id: playerId,
      sou_desenhista: currentGameState?.current_drawer === playerId,
    });

    isWaitingForWord = false; // Reseta o flag quando recebe a palavra

    // Verifica se é realmente o desenhista atual usando o estado do jogo
    if (currentGameState?.current_drawer === playerId) {
      console.log("Sou o desenhista atual, habilitando controles de desenho");
      canDraw = true;
      drawingControls.classList.remove("hidden");
      gameControls.classList.add("hidden");
      gameStatus.textContent = `Sua vez de desenhar: "${data.word}"`;
      gameStatus.classList.remove("hidden");
    } else {
      console.log("Não sou o desenhista atual");
      canDraw = false;
      drawingControls.classList.add("hidden");
      gameControls.classList.remove("hidden");
      gameStatus.textContent = "Adivinhe o desenho!";
      gameStatus.classList.remove("hidden");
    }
  });

  socket.on("draw_data", (data) => {
    console.log("Recebendo dados de desenho", data);
    const points = data.points;
    ctx.beginPath();
    ctx.moveTo(points.x0, points.y0);
    ctx.lineTo(points.x1, points.y1);
    ctx.strokeStyle = data.color;
    ctx.lineWidth = data.thickness;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();
  });

  socket.on("correct_guess", (data) => {
    console.log("Acerto! Novo estado:", data);
    // Limpa o canvas para todos os jogadores
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Reseta os controles e estados
    drawingControls.classList.add("hidden");
    gameControls.classList.add("hidden");
    canDraw = false;
    isWaitingForWord = false; // Reseta o flag em caso de acerto

    // Mostra mensagem de acerto
    if (data.player_id === playerId) {
      gameStatus.textContent = "Parabéns! Você acertou!";
    } else {
      const guesserName = data.game_state.players[data.player_id].name;
      gameStatus.textContent = `${guesserName} acertou a palavra!`;
    }
    gameStatus.classList.remove("hidden");

    // Atualiza o estado do jogo após a mensagem de acerto
    setTimeout(() => {
      // Atualiza o estado do jogo
      updateGameState(data.game_state);

      // Verifica se é o novo desenhista
      if (data.game_state.current_drawer === playerId) {
        console.log(
          "Sou o novo desenhista após acerto, solicitando palavra..."
        );
        requestWord();
      } else {
        drawingControls.classList.add("hidden");
        gameControls.classList.remove("hidden");
        gameStatus.textContent = "Aguardando o próximo desenho...";
        gameStatus.classList.remove("hidden");
      }
    }, 3000);
  });

  socket.on("player_disconnected", (data) => {
    updateGameState(data.game_state);
  });

  socket.on("error", (data) => {
    alert(data.message);
  });

  // Funções de Atualização da Interface
  function updateGameState(gameState) {
    console.log("Atualizando estado do jogo", gameState);

    // Atualiza o estado atual do jogo
    currentGameState = gameState;

    // Atualiza os times
    teamAPlayers.innerHTML = "";
    teamBPlayers.innerHTML = "";

    for (const pid in gameState.players) {
      const player = gameState.players[pid];
      const playerElement = document.createElement("li");
      playerElement.textContent = `${player.name} (${player.score} pontos)`;

      // Destaca o desenhista atual
      if (pid === gameState.current_drawer) {
        playerElement.textContent += " (Desenhando)";
        playerElement.style.fontWeight = "bold";
      }

      if (player.team === "A") {
        teamAPlayers.appendChild(playerElement);
      } else if (player.team === "B") {
        teamBPlayers.appendChild(playerElement);
      }
    }

    // Atualiza pontuações
    teamAScore.textContent = gameState.scores.A;
    teamBScore.textContent = gameState.scores.B;

    // Atualiza controles de desenho e palpites
    if (gameState.game_started) {
      console.log("Verificando permissão de desenho", {
        currentDrawer: gameState.current_drawer,
        playerId: playerId,
        canDraw: gameState.current_drawer === playerId,
        isWaitingForWord: isWaitingForWord,
      });

      if (
        gameState.current_drawer === playerId &&
        !canDraw &&
        !isWaitingForWord
      ) {
        // Se for o novo desenhista mas ainda não recebeu a palavra e não está aguardando
        console.log(
          "Sou o desenhista atual mas ainda não tenho a palavra, solicitando..."
        );
        requestWord();
      } else if (gameState.current_drawer !== playerId) {
        // Se não for o desenhista
        canDraw = false;
        drawingControls.classList.add("hidden");
        gameControls.classList.remove("hidden");
        gameStatus.textContent = "Adivinhe o desenho!";
        gameStatus.classList.remove("hidden");
      }
    }
  }

  function updateWaitingRoom(gameState) {
    waitingPlayers.innerHTML = "";
    const players = Object.values(gameState.players);

    players.forEach((player) => {
      const playerElement = document.createElement("li");
      playerElement.className = "list-group-item";
      playerElement.textContent = player.name;
      if (player.id === playerId) {
        playerElement.className += " active";
      }
      waitingPlayers.appendChild(playerElement);
    });
  }

  // Copiar código da sala
  copyRoomCode.addEventListener("click", () => {
    const roomCode = currentRoom;
    navigator.clipboard.writeText(roomCode).then(() => {
      const originalText = copyRoomCode.textContent;
      copyRoomCode.textContent = "Copiado!";
      setTimeout(() => {
        copyRoomCode.textContent = originalText;
      }, 2000);
    });
  });

  // Eventos de redimensionamento
  window.addEventListener("resize", () => {
    console.log("Janela redimensionada");
    resizeCanvas();
  });

  // Inicialização inicial
  console.log("DOM carregado");
  if (!gameSection.classList.contains("hidden")) {
    initializeCanvas();
  }
});
