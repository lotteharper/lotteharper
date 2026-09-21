(function threeThirteen() {
  "use strict";

  const PLAYER_ONE = "Player 1";
  const PLAYER_TWO = "Player 2";

  const CARD_NAMES = [
    "A", "2", "3", "4", "5", "6", "7",
    "8", "9", "10", "J", "Q", "K"
  ];

  const SUITS = ["S", "H", "C", "D"];
  const CARD_ROOT = "https://lotteh.com/media/games/cards/";
  const CARD_SCALE = 0.9;

  const postElement = document.getElementById("post_id");
  const codeElement = document.getElementById("game_code");
  const gameElement = document.getElementById("game_id");
  const playerElement = document.getElementById("player");
  const canvas = document.getElementById("game");

  if (
    !postElement ||
    !codeElement ||
    !gameElement ||
    !playerElement ||
    !canvas ||
    typeof createjs === "undefined"
  ) {
    return;
  }

  const postUuid = postElement.innerHTML.trim();
  const gameCode = codeElement.innerHTML.trim();
  const gameId = String(gameElement.innerHTML).trim();

  const user = playerElement.innerHTML.trim() === "y"
    ? PLAYER_ONE
    : PLAYER_TWO;

  const opponent = user === PLAYER_ONE
    ? PLAYER_TWO
    : PLAYER_ONE;

  const adElement = document.getElementById("dontshowad");
  const adHeight =
    adElement &&
    adElement.innerHTML.trim() === "true"
      ? 0
      : 120;

  const TEXT = "bold 42px Arial";
  const SMALL_TEXT = "bold 30px Arial";
  const LARGE_TEXT = "bold 70px Arial";

  const cardImages = [];
  const backImage = new Image();

  let imagesLoaded = 0;
  let started = false;

  let socket = null;
  let reconnectTimer = null;

  let stateReceived = false;
  let gameReady = false;

  let currentRound = 3;
  let currentCard = 0;
  let deck = [];

  let playerCards = [];
  let playerSuits = [];
  let opponentCards = [];
  let opponentSuits = [];

  let discardCards = [];
  let discardSuits = [];

  let canDraw = false;
  let canDiscard = false;
  let roundComplete = false;
  let gameFinished = false;
  let pendingWinner = null;
  let roundKey = "";

  let playerScore = 0;
  let opponentScore = 0;
  let history = [];

  let roundSettlement = false;
  let roundWinner = null;
  let settlementActionSent = false;

  let playerObjects = [];
  let opponentObjects = [];
  let deckBitmap = null;
  let discardBitmap = null;
  let roundDialog = null;
  let joinDialog = null;

  let playerScoreText = null;
  let opponentScoreText = null;
  let currentPlayerText = null;
  let roundText = null;

  const stage = new createjs.Stage(canvas);
  const background = new createjs.Shape();
  const container = new createjs.Container();

  stage.addChild(background);
  stage.addChild(container);

  let leftBound = 0;
  let topBound = 0;
  let boardSize = 0;

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = Math.max(0, window.innerHeight - adHeight);

    background.graphics.clear();
    background.graphics
      .beginFill("#b0afb3")
      .drawRect(0, 0, canvas.width, canvas.height);

    boardSize = Math.min(canvas.width, canvas.height);

    if (boardSize <= 0) {
      stage.update();
      return;
    }

    container.scaleX = boardSize / 1000;
    container.scaleY = boardSize / 1000;

    leftBound =
      (canvas.width - boardSize) /
      2 /
      container.scaleX;

    topBound =
      (canvas.height - boardSize) /
      2 /
      container.scaleY;

    stage.update();
  }

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  /*
   * ----------------------------------------------------------------------
   * Wildcards
   * ----------------------------------------------------------------------
   */

  function getWildcardValue() {
    return currentRound - 1;
  }

  function isWildcardValue(value) {
    return Number(value) === getWildcardValue();
  }

  function isWildcardCard(value, suit) {
    return (
      isWildcardValue(value) &&
      Number(suit) >= 0 &&
      Number(suit) < 4
    );
  }

  /*
   * ----------------------------------------------------------------------
   * Card deck and dealing
   * ----------------------------------------------------------------------
   */

  function RNG(seed) {
    this.state = seed >>> 0;
  }

  RNG.prototype.next = function() {
    this.state =
      (1664525 * this.state + 1013904223) >>> 0;
    return this.state;
  };

  RNG.prototype.range = function(min, max) {
    return min + this.next() % (max - min);
  };

  function makeDeck(round) {
    const cards = [];
    const rng = new RNG(
      (10000 + Number(gameId || 0) + round * 7919) >>> 0
    );

    for (let suit = 0; suit < 4; suit++) {
      for (let value = 0; value < 13; value++) {
        cards.push({ value, suit });
      }
    }

    for (let i = cards.length - 1; i > 0; i--) {
      const j = rng.range(0, i + 1);
      [cards[i], cards[j]] = [cards[j], cards[i]];
    }

    return cards;
  }

  function getDeckCard(index) {
    if (!deck[index]) {
      return null;
    }

    return {
      value: deck[index].value,
      suit: deck[index].suit
    };
  }

  function addCard(cards, suits, card) {
    if (!card) {
      return false;
    }

    cards.push(card.value);
    suits.push(card.suit);
    return true;
  }

  function getRoundStarter(round) {
    return round % 2 === 1
      ? PLAYER_ONE
      : PLAYER_TWO;
  }

  function sortCards(cards, suits, byValue) {
    const combined = cards.map(function(value, index) {
      return {
        value,
        suit: suits[index]
      };
    });

    combined.sort(function(a, b) {
      if (byValue && a.value !== b.value) {
        return b.value - a.value;
      }

      if (a.suit !== b.suit) {
        return b.suit - a.suit;
      }

      return b.value - a.value;
    });

    return {
      cards: combined.map(item => item.value),
      suits: combined.map(item => item.suit)
    };
  }

  function dealRound(round) {
    currentRound = Math.max(
      3,
      Math.min(13, Number(round) || 3)
    );

    deck = makeDeck(currentRound);

    playerCards = [];
    playerSuits = [];
    opponentCards = [];
    opponentSuits = [];
    discardCards = [];
    discardSuits = [];

    for (let i = 0; i < currentRound; i++) {
      const first = getDeckCard(i);
      const second = getDeckCard(currentRound + i);

      if (user === PLAYER_ONE) {
        addCard(playerCards, playerSuits, first);
        addCard(opponentCards, opponentSuits, second);
      } else {
        addCard(opponentCards, opponentSuits, first);
        addCard(playerCards, playerSuits, second);
      }
    }

    const openingDiscard = getDeckCard(currentRound * 2);

    if (openingDiscard) {
      discardCards.push(openingDiscard.value);
      discardSuits.push(openingDiscard.suit);
    }

    currentCard = currentRound * 2 + 1;

    let sorted = sortCards(
      playerCards,
      playerSuits,
      true
    );

    playerCards = sorted.cards;
    playerSuits = sorted.suits;

    sorted = sortCards(
      opponentCards,
      opponentSuits,
      true
    );

    opponentCards = sorted.cards;
    opponentSuits = sorted.suits;

    roundComplete = false;
    roundKey = "";
    pendingWinner = null;

    canDiscard = false;
    canDraw = getRoundStarter(currentRound) === user;

    setRoundText();
    setCurrentPlayer(canDraw);
    redrawAll();
  }

  function resetNewGame() {
    currentRound = 3;
    currentCard = 0;
    deck = [];

    playerCards = [];
    playerSuits = [];
    opponentCards = [];
    opponentSuits = [];
    discardCards = [];
    discardSuits = [];

    playerScore = 0;
    opponentScore = 0;

    canDraw = false;
    canDiscard = false;
    roundComplete = false;
    gameFinished = false;
    pendingWinner = null;
    roundKey = "";
    roundSettlement = false;
    roundWinner = null;
    settlementActionSent = false;
    history = [];

    drawPlayerScore("--");
    drawOpponentScore("--");

    dealRound(3);
  }

  /*
   * ----------------------------------------------------------------------
   * Rendering
   * ----------------------------------------------------------------------
   */

  function clearObjects(objects) {
    objects.forEach(function(object) {
      if (object && container.contains(object)) {
        container.removeChild(object);
      }
    });

    objects.length = 0;
  }

  function drawCard(suit, value, x, y) {
    if (
      !cardImages[suit] ||
      !cardImages[suit][value]
    ) {
      return null;
    }

    const bitmap = new createjs.Bitmap(
      cardImages[suit][value]
    );

    bitmap.scaleX = CARD_SCALE;
    bitmap.scaleY = CARD_SCALE;
    bitmap.x = leftBound + x - 125 * CARD_SCALE;
    bitmap.y = topBound + y - 175 * CARD_SCALE;

    container.addChild(bitmap);
    return bitmap;
  }

  function drawFaceDownCard(x, y) {
    const bitmap = new createjs.Bitmap(backImage);

    bitmap.scaleX = CARD_SCALE;
    bitmap.scaleY = CARD_SCALE;
    bitmap.x = leftBound + x - 125 * CARD_SCALE;
    bitmap.y = topBound + y - 175 * CARD_SCALE;

    container.addChild(bitmap);
    return bitmap;
  }

  function drawWildcardMarker(bitmap) {
    const marker = new createjs.Text(
      "WILD",
      "bold 18px Arial",
      "#8a0010"
    );

    marker.x = bitmap.x + 28;
    marker.y = bitmap.y + 24;
    marker.textAlign = "center";
    marker.mouseEnabled = false;

    container.addChild(marker);
    return marker;
  }

  function drawPlayerHand() {
    clearObjects(playerObjects);

    for (let i = playerCards.length - 1; i >= 0; i--) {
      const row = i > 6 ? 140 : 30;
      const offset = i > 6 ? 7 : 0;
      const x = 1000 - (1000 / 7) * (i - offset);
      const y = 1000 - row;

      const bitmap = drawCard(
        playerSuits[i],
        playerCards[i],
        x,
        y
      );

      if (!bitmap) {
        continue;
      }

      bitmap.value = playerCards[i];
      bitmap.suit = playerSuits[i];
      playerObjects.push(bitmap);

      if (isWildcardCard(bitmap.value, bitmap.suit)) {
        bitmap.alpha = 0.92;
        playerObjects.push(drawWildcardMarker(bitmap));
      }

      bitmap.on("mousedown", function(event) {
        if (
          !gameReady ||
          gameFinished ||
          !canDiscard ||
          playerCards.length !== currentRound + 1
        ) {
          return;
        }

        if (
          roundSettlement &&
          roundWinner === user
        ) {
          return;
        }

        const value = event.currentTarget.value;
        const suit = event.currentTarget.suit;

        if (isWildcardCard(value, suit)) {
          return;
        }

        if (!discardPlayerCard(value, suit)) {
          return;
        }

        if (!sendAction(
          "discard," +
          value +
          "." +
          suit +
          "," +
          user
        )) {
          return;
        }

        if (
          !roundSettlement &&
          pendingWinner === user
        ) {
          sendAction(
            "round_complete," +
            currentRound +
            "," +
            user
          );
          pendingWinner = null;
        }

        if (
          roundSettlement &&
          roundWinner !== user
        ) {
          completeSettlementTurn();
        }
      });
    }

    stage.update();
  }

  function drawOpponentHand(faceUp) {
    clearObjects(opponentObjects);

    for (let i = 0; i < opponentCards.length; i++) {
      const row = i > 6 ? 140 : 30;
      const offset = i > 6 ? 7 : 0;
      const x =
        1000 -
        (1000 / 7) *
        (i - offset + 1);

      const bitmap = faceUp
        ? drawCard(
            opponentSuits[i],
            opponentCards[i],
            x,
            row
          )
        : drawFaceDownCard(x, row);

      if (!bitmap) {
        continue;
      }

      opponentObjects.push(bitmap);

      if (
        faceUp &&
        isWildcardCard(
          opponentCards[i],
          opponentSuits[i]
        )
      ) {
        bitmap.alpha = 0.92;
        opponentObjects.push(drawWildcardMarker(bitmap));
      }
    }

    stage.update();
  }

  function drawDeck() {
    if (deckBitmap && container.contains(deckBitmap)) {
      container.removeChild(deckBitmap);
    }

    deckBitmap = drawFaceDownCard(300, 500);
    deckBitmap.mouseEnabled = true;

    deckBitmap.on("mousedown", function() {
      if (
        !gameReady ||
        gameFinished ||
        !canDraw ||
        playerCards.length !== currentRound
      ) {
        return;
      }

      if (
        roundSettlement &&
        roundWinner === user
      ) {
        return;
      }

      if (drawPlayerFromDeck(false)) {
        sendAction("draw,deck," + user);
      }
    });
  }

  function drawDiscard() {
    if (discardBitmap && container.contains(discardBitmap)) {
      container.removeChild(discardBitmap);
    }

    discardBitmap = null;

    if (discardCards.length === 0) {
      stage.update();
      return;
    }

    const index = discardCards.length - 1;

    discardBitmap = drawCard(
      discardSuits[index],
      discardCards[index],
      700,
      500
    );

    if (!discardBitmap) {
      return;
    }

    if (
      isWildcardCard(
        discardCards[index],
        discardSuits[index]
      )
    ) {
      discardBitmap.alpha = 0.94;
      drawWildcardMarker(discardBitmap);
    }

    discardBitmap.mouseEnabled = true;

    discardBitmap.on("mousedown", function() {
      if (
        !gameReady ||
        gameFinished ||
        !canDraw ||
        playerCards.length !== currentRound
      ) {
        return;
      }

      if (
        roundSettlement &&
        roundWinner === user
      ) {
        return;
      }

      if (drawPlayerFromDiscard(false)) {
        sendAction("draw,discard," + user);
      }
    });

    stage.update();
  }

  function redrawAll() {
    drawPlayerHand();
    drawOpponentHand(false);
    drawDeck();
    drawDiscard();
    stage.update();
  }

  function drawInterface() {
    const radius = 10;
    const size = 100;

    const playerPanel = new createjs.Shape();
    playerPanel.graphics
      .beginFill("lightyellow")
      .drawRoundRect(
        leftBound,
        topBound + 550,
        size,
        size,
        radius
      );

    const opponentPanel = new createjs.Shape();
    opponentPanel.graphics
      .beginFill("#f0655b")
      .drawRoundRect(
        leftBound,
        topBound + 350,
        size,
        size,
        radius
      );

    playerScoreText = new createjs.Text("--", TEXT, "#000000");
    playerScoreText.x = leftBound + 50;
    playerScoreText.y = topBound + 580;
    playerScoreText.textAlign = "center";

    opponentScoreText = new createjs.Text("--", TEXT, "#000000");
    opponentScoreText.x = leftBound + 50;
    opponentScoreText.y = topBound + 380;
    opponentScoreText.textAlign = "center";

    currentPlayerText = new createjs.Text(
      "☆",
      LARGE_TEXT,
      "#E8CD71"
    );
    currentPlayerText.x = leftBound + 50;
    currentPlayerText.textAlign = "center";

    const circle = new createjs.Shape();
    circle.graphics
      .beginFill("#E8CD71")
      .drawCircle(0, 0, 50);
    circle.x = leftBound + 500;
    circle.y = topBound + 500;

    roundText = new createjs.Text(
      "",
      LARGE_TEXT,
      "#000000"
    );
    roundText.x = leftBound + 500;
    roundText.y = topBound + 470;
    roundText.textAlign = "center";

    container.addChild(playerPanel);
    container.addChild(opponentPanel);
    container.addChild(playerScoreText);
    container.addChild(opponentScoreText);
    container.addChild(currentPlayerText);
    container.addChild(circle);
    container.addChild(roundText);

    drawSortButtons();
    setRoundText();
    setCurrentPlayer(getRoundStarter(currentRound) === user);
  }

  function drawSortButtons() {
    const radius = 10;
    const size = 100;

    const suitButton = new createjs.Shape();
    suitButton.graphics
      .beginFill("lightgreen")
      .drawRoundRect(
        leftBound + 900,
        topBound + 350,
        size,
        size,
        radius
      );

    const suitText = new createjs.Text("333", TEXT, "#000000");
    suitText.x = leftBound + 950;
    suitText.y = topBound + 380;
    suitText.textAlign = "center";

    suitButton.on("mousedown", function() {
      const sorted = sortCards(
        playerCards,
        playerSuits,
        false
      );

      playerCards = sorted.cards;
      playerSuits = sorted.suits;
      drawPlayerHand();
    });

    const valueButton = new createjs.Shape();
    valueButton.graphics
      .beginFill("lightblue")
      .drawRoundRect(
        leftBound + 900,
        topBound + 550,
        size,
        size,
        radius
      );

    const valueText = new createjs.Text("456", TEXT, "#000000");
    valueText.x = leftBound + 950;
    valueText.y = topBound + 580;
    valueText.textAlign = "center";

    valueButton.on("mousedown", function() {
      const sorted = sortCards(
        playerCards,
        playerSuits,
        true
      );

      playerCards = sorted.cards;
      playerSuits = sorted.suits;
      drawPlayerHand();
    });

    container.addChild(suitButton);
    container.addChild(suitText);
    container.addChild(valueButton);
    container.addChild(valueText);
  }

  function setCurrentPlayer(mayDraw) {
    if (currentPlayerText) {
      currentPlayerText.y = mayDraw
        ? topBound + 670
        : topBound + 270;
    }
  }

  function setRoundText() {
    if (roundText) {
      roundText.text =
        CARD_NAMES[currentRound - 1] ||
        String(currentRound);
    }
  }

  function drawPlayerScore(value) {
    if (playerScoreText) {
      playerScoreText.text = String(value);
    }
  }

  function drawOpponentScore(value) {
    if (opponentScoreText) {
      opponentScoreText.text = String(value);
    }
  }

  /*
   * ----------------------------------------------------------------------
   * Turn operations
   * ----------------------------------------------------------------------
   */

  function setTurnAfterAction(type, actor) {
    const localActor = actor === user;

    if (type === "draw") {
      canDraw = false;
      canDiscard = localActor;
      setCurrentPlayer(false);
      return;
    }

    if (type === "discard") {
      canDraw = !localActor;
      canDiscard = false;
      setCurrentPlayer(!localActor);
    }
  }

  function recycleDiscard() {
    if (discardCards.length <= 1) {
      return false;
    }

    const top = discardCards.length - 1;
    const recycled = [];

    for (let i = 0; i < top; i++) {
      recycled.push({
        value: discardCards[i],
        suit: discardSuits[i]
      });
    }

    deck = recycled;
    currentCard = 0;

    discardCards = [discardCards[top]];
    discardSuits = [discardSuits[top]];

    drawDiscard();
    return true;
  }

  function losingPlayerMaySettle() {
    return (
      roundSettlement &&
      roundWinner &&
      roundWinner !== user &&
      !gameFinished
    );
  }

  function drawPlayerFromDeck(replayMode) {
    if (
      !replayMode &&
      (
        !canDraw ||
        gameFinished ||
        (
          roundComplete &&
          !losingPlayerMaySettle()
        )
      )
    ) {
      return false;
    }

    if (playerCards.length !== currentRound) {
      return false;
    }

    if (currentCard >= deck.length && !recycleDiscard()) {
      return false;
    }

    const card = getDeckCard(currentCard);

    if (!card) {
      return false;
    }

    currentCard++;
    addCard(playerCards, playerSuits, card);

    if (!replayMode) {
      canDraw = false;
      canDiscard = true;
      setCurrentPlayer(false);
    }

    drawPlayerHand();
    return true;
  }

  function drawPlayerFromDiscard(replayMode) {
    if (
      !replayMode &&
      (
        !canDraw ||
        gameFinished ||
        (
          roundComplete &&
          !losingPlayerMaySettle()
        )
      )
    ) {
      return false;
    }

    if (
      playerCards.length !== currentRound ||
      discardCards.length === 0
    ) {
      return false;
    }

    const index = discardCards.length - 1;

    addCard(
      playerCards,
      playerSuits,
      {
        value: discardCards[index],
        suit: discardSuits[index]
      }
    );

    discardCards.pop();
    discardSuits.pop();

    if (!replayMode) {
      canDraw = false;
      canDiscard = true;
      setCurrentPlayer(false);
    }

    drawPlayerHand();
    drawDiscard();

    return true;
  }

  function drawOpponentFromDeck(replayMode) {
    if (opponentCards.length !== currentRound) {
      return false;
    }

    if (currentCard >= deck.length && !recycleDiscard()) {
      return false;
    }

    const card = getDeckCard(currentCard);

    if (!card) {
      return false;
    }

    currentCard++;
    addCard(opponentCards, opponentSuits, card);

    if (!replayMode) {
      setTurnAfterAction("draw", opponent);
    }

    drawOpponentHand(false);
    return true;
  }

  function drawOpponentFromDiscard(replayMode) {
    if (
      opponentCards.length !== currentRound ||
      discardCards.length === 0
    ) {
      return false;
    }

    const index = discardCards.length - 1;

    addCard(
      opponentCards,
      opponentSuits,
      {
        value: discardCards[index],
        suit: discardSuits[index]
      }
    );

    discardCards.pop();
    discardSuits.pop();

    if (!replayMode) {
      setTurnAfterAction("draw", opponent);
    }

    drawOpponentHand(false);
    drawDiscard();

    return true;
  }

  function completeSettlementTurn() {
    if (
      !roundSettlement ||
      settlementActionSent ||
      gameFinished ||
      roundWinner === user
    ) {
      return false;
    }

    settlementActionSent = true;

    const sent = sendAction(
      "round_advance," +
      currentRound +
      "," +
      user
    );

    if (!sent) {
      settlementActionSent = false;
      return false;
    }

    advanceRound();
    return true;
  }

  function discardPlayerCard(value, suit) {
    if (
      !gameReady ||
      gameFinished ||
      !canDiscard ||
      playerCards.length !== currentRound + 1
    ) {
      return false;
    }

    if (
      roundSettlement &&
      roundWinner === user
    ) {
      return false;
    }

    if (isWildcardCard(value, suit)) {
      return false;
    }

    const index = playerCards.findIndex(function(card, i) {
      return (
        card === value &&
        playerSuits[i] === suit
      );
    });

    if (index < 0) {
      return false;
    }

    playerCards.splice(index, 1);
    playerSuits.splice(index, 1);

    discardCards.push(value);
    discardSuits.push(suit);

    canDraw = false;
    canDiscard = false;

    drawPlayerHand();
    drawDiscard();

    if (roundSettlement) {
      return true;
    }

    setCurrentPlayer(false);

    const score = calculateScore(
      playerCards,
      playerSuits
    );

    pendingWinner =
      playerCards.length === currentRound &&
      score === 0
        ? user
        : null;

    return true;
  }

  function discardPlayerDuringReplay(value, suit) {
    const index = playerCards.findIndex(function(card, i) {
      return (
        card === value &&
        playerSuits[i] === suit
      );
    });

    if (index < 0) {
      return false;
    }

    playerCards.splice(index, 1);
    playerSuits.splice(index, 1);
    discardCards.push(value);
    discardSuits.push(suit);

    drawPlayerHand();
    drawDiscard();
    return true;
  }

  function discardOpponentCard(value, suit) {
    if (isWildcardCard(value, suit)) {
      return false;
    }

    const index = opponentCards.findIndex(function(card, i) {
      return (
        card === value &&
        opponentSuits[i] === suit
      );
    });

    if (index < 0) {
      return false;
    }

    opponentCards.splice(index, 1);
    opponentSuits.splice(index, 1);
    discardCards.push(value);
    discardSuits.push(suit);

    drawOpponentHand(false);
    drawDiscard();
    return true;
  }

  /*
   * ----------------------------------------------------------------------
   * Scoring
   * ----------------------------------------------------------------------
   */

  function calculateScore(cards, suits) {
    const counts = [];
    let wildcards = 0;

    for (let suit = 0; suit < 4; suit++) {
      counts[suit] = [];

      for (let value = 0; value < 13; value++) {
        counts[suit][value] = 0;
      }
    }

    for (let i = 0; i < cards.length; i++) {
      if (isWildcardValue(cards[i])) {
        wildcards++;
      } else if (
        Number.isInteger(suits[i]) &&
        suits[i] >= 0 &&
        suits[i] < 4 &&
        Number.isInteger(cards[i]) &&
        cards[i] >= 0 &&
        cards[i] < 13
      ) {
        counts[suits[i]][cards[i]]++;
      }
    }

    const memo = new Map();

    function cloneCounts(state) {
      return state.map(row => row.slice());
    }

    function makeKey(state, wild) {
      return (
        wild +
        ":" +
        state.map(row => row.join("")).join("|")
      );
    }

    function deadwoodValue(value) {
      return Math.min(value + 1, 10);
    }

    function findFirstCard(state) {
      for (let suit = 0; suit < 4; suit++) {
        for (let value = 0; value < 13; value++) {
          if (state[suit][value] > 0) {
            return { suit, value };
          }
        }
      }

      return null;
    }

    function solve(state, wild) {
      const key = makeKey(state, wild);

      if (memo.has(key)) {
        return memo.get(key);
      }

      const firstCard = findFirstCard(state);

      if (!firstCard) {
        let best = wild * 3;

        for (
          let meldSize = 3;
          meldSize <= 4 && meldSize <= wild;
          meldSize++
        ) {
          best = Math.min(
            best,
            solve(state, wild - meldSize)
          );
        }

        memo.set(key, best);
        return best;
      }

      let best = deadwoodValue(firstCard.value);

      const sameValueSuits = [];

      for (let suit = 0; suit < 4; suit++) {
        if (state[suit][firstCard.value] > 0) {
          sameValueSuits.push(suit);
        }
      }

      for (
        let mask = 1;
        mask < (1 << sameValueSuits.length);
        mask++
      ) {
        if (!(mask & 1)) {
          continue;
        }

        const selected = [];

        for (
          let bit = 0;
          bit < sameValueSuits.length;
          bit++
        ) {
          if (mask & (1 << bit)) {
            selected.push(sameValueSuits[bit]);
          }
        }

        for (
          let usedWildcards = 0;
          usedWildcards <= 4 && usedWildcards <= wild;
          usedWildcards++
        ) {
          const meldSize = selected.length + usedWildcards;

          if (meldSize < 3) {
            continue;
          }

          const next = cloneCounts(state);

          selected.forEach(function(suit) {
            next[suit][firstCard.value]--;
          });

          best = Math.min(
            best,
            solve(next, wild - usedWildcards)
          );
        }
      }

      for (let length = 3; length <= 13; length++) {
        const minimumStart = Math.max(
          0,
          firstCard.value - length + 1
        );

        const maximumStart = Math.min(
          firstCard.value,
          13 - length
        );

        for (
          let start = minimumStart;
          start <= maximumStart;
          start++
        ) {
          const next = cloneCounts(state);
          let missing = 0;

          for (
            let value = start;
            value < start + length;
            value++
          ) {
            if (next[firstCard.suit][value] > 0) {
              next[firstCard.suit][value]--;
            } else {
              missing++;
            }
          }

          if (missing > wild || missing > 4) {
            continue;
          }

          for (
            let usedWildcards = missing;
            usedWildcards <= 4 && usedWildcards <= wild;
            usedWildcards++
          ) {
            best = Math.min(
              best,
              solve(next, wild - usedWildcards)
            );
          }
        }
      }

      for (
        let meldSize = 3;
        meldSize <= 4 && meldSize <= wild;
        meldSize++
      ) {
        best = Math.min(
          best,
          solve(state, wild - meldSize)
        );
      }

      memo.set(key, best);
      return best;
    }

    return solve(counts, wildcards);
  }

  /*
   * ----------------------------------------------------------------------
   * Round completion and settlement
   * ----------------------------------------------------------------------
   */

  function finishRound(winner) {
    const key = currentRound + ":" + winner;

    if (
      gameFinished ||
      roundKey === key
    ) {
      return;
    }

    roundKey = key;
    roundWinner = winner;
    roundSettlement = true;
    roundComplete = true;
    settlementActionSent = false;

    playerScore += calculateScore(
      playerCards,
      playerSuits
    );

    opponentScore += calculateScore(
      opponentCards,
      opponentSuits
    );

    drawPlayerScore(playerScore);
    drawOpponentScore(opponentScore);

    if (currentRound >= 13) {
      gameFinished = true;
      canDraw = false;
      canDiscard = false;
      drawFinishedDialog();
      return;
    }

    const loserMayDraw = winner !== user;

    canDraw = loserMayDraw;
    canDiscard = false;

    showRoundSettlementDialog(winner);
    setCurrentPlayer(loserMayDraw);
    stage.update();
  }

  function advanceRound() {
    if (
      gameFinished ||
      !roundSettlement ||
      currentRound >= 13
    ) {
      return false;
    }

    removeRoundDialog();

    const nextRound = currentRound + 1;

    currentRound = nextRound;
    currentCard = 0;

    roundSettlement = false;
    roundWinner = null;
    settlementActionSent = false;
    roundComplete = false;
    roundKey = "";
    pendingWinner = null;

    canDraw = getRoundStarter(currentRound) === user;
    canDiscard = false;

    dealRound(currentRound);
    setCurrentPlayer(canDraw);
    redrawAll();

    return true;
  }

  function showRoundSettlementDialog(winner) {
    removeRoundDialog();

    roundDialog = new createjs.Container();
    roundDialog.mouseEnabled = false;
    roundDialog.mouseChildren = false;

    const panel = new createjs.Shape();
    panel.graphics
      .beginFill(
        winner === user
          ? "lightgreen"
          : "lightblue"
      )
      .drawRoundRect(
        leftBound + 100,
        topBound + 300,
        800,
        340,
        25
      );

    panel.mouseEnabled = false;

    const message = new createjs.Text(
      winner === user
        ? "You won the round"
        : "Your opponent won the round",
      TEXT,
      "#000000"
    );

    message.x = leftBound + 500;
    message.y = topBound + 360;
    message.textAlign = "center";
    message.mouseEnabled = false;

    const detail = new createjs.Text(
      winner === user
        ? "Your opponent may take one final turn"
        : "You may take one final turn",
      SMALL_TEXT,
      "#000000"
    );

    detail.x = leftBound + 500;
    detail.y = topBound + 455;
    detail.textAlign = "center";
    detail.mouseEnabled = false;

    const instruction = new createjs.Text(
      winner === user
        ? "Waiting for opponent..."
        : "Draw and discard to continue",
      SMALL_TEXT,
      "#000000"
    );

    instruction.x = leftBound + 500;
    instruction.y = topBound + 525;
    instruction.textAlign = "center";
    instruction.mouseEnabled = false;

    roundDialog.addChild(
      panel,
      message,
      detail,
      instruction
    );

    container.addChildAt(
      roundDialog,
      Math.max(0, container.getNumChildren() - 1)
    );

    if (winner === user) {
      drawPlayerHand();
      drawOpponentHand(false);
    } else {
      drawPlayerHand();
      drawOpponentHand(true);
    }

    stage.update();
  }

  function removeRoundDialog() {
    if (
      roundDialog &&
      container.contains(roundDialog)
    ) {
      container.removeChild(roundDialog);
    }

    roundDialog = null;
  }

  function drawFinishedDialog() {
    removeRoundDialog();

    const panel = new createjs.Shape();
    panel.graphics
      .beginFill("#f4f0d0")
      .drawRoundRect(
        leftBound + 100,
        topBound + 250,
        800,
        500,
        25
      );

    const title = new createjs.Text(
      "Game complete",
      TEXT,
      "#000000"
    );
    title.x = leftBound + 500;
    title.y = topBound + 300;
    title.textAlign = "center";

    const result =
      playerScore < opponentScore
        ? "You won!"
        : playerScore > opponentScore
          ? "Your opponent won!"
          : "It's a tie!";

    const resultText = new createjs.Text(
      result,
      TEXT,
      "#000000"
    );
    resultText.x = leftBound + 500;
    resultText.y = topBound + 410;
    resultText.textAlign = "center";

    const scores = new createjs.Text(
      PLAYER_ONE + ": " +
      (user === PLAYER_ONE ? playerScore : opponentScore) +
      "\n" +
      PLAYER_TWO + ": " +
      (user === PLAYER_TWO ? playerScore : opponentScore),
      SMALL_TEXT,
      "#000000"
    );

    scores.x = leftBound + 500;
    scores.y = topBound + 520;
    scores.textAlign = "center";
    scores.lineHeight = 60;

    container.addChild(panel);
    container.addChild(title);
    container.addChild(resultText);
    container.addChild(scores);
    stage.update();
  }

  /*
   * ----------------------------------------------------------------------
   * History / protocol
   * ----------------------------------------------------------------------
   */

  function normaliseAction(value) {
    return String(value || "")
      .trim()
      .replace(/\/+$/, "");
  }

  function isReplayableAction(action) {
    action = normaliseAction(action);

    if (!action) {
      return false;
    }

    const parts = action.split(",");
    const type = parts[0];

    if (
      type === "join" ||
      type === "x" ||
      type === "y" ||
      type === "<SCORE>"
    ) {
      return false;
    }

    if (type === "draw") {
      return (
        parts.length === 3 &&
        (
          parts[1] === "deck" ||
          parts[1] === "discard"
        ) &&
        Boolean(parts[2])
      );
    }

    if (type === "discard") {
      if (parts.length !== 3) {
        return false;
      }

      const cardParts = parts[1].split(".");
      const value = Number(cardParts[0]);
      const suit = Number(cardParts[1]);

      return (
        cardParts.length === 2 &&
        Number.isInteger(value) &&
        Number.isInteger(suit) &&
        value >= 0 &&
        value < 13 &&
        suit >= 0 &&
        suit < 4 &&
        Boolean(parts[2])
      );
    }

    if (type === "round_complete") {
      const roundNumber = Number(parts[1]);

      return (
        parts.length === 3 &&
        Number.isInteger(roundNumber) &&
        roundNumber >= 3 &&
        roundNumber <= 13 &&
        Boolean(parts[2])
      );
    }

    if (type === "round_advance") {
      const roundNumber = Number(parts[1]);

      return (
        parts.length === 3 &&
        Number.isInteger(roundNumber) &&
        roundNumber >= 3 &&
        roundNumber <= 13 &&
        Boolean(parts[2])
      );
    }

    return false;
  }

  function setTurnAfterAction(type, actor) {
    const localActor = actor === user;

    if (type === "draw") {
      canDraw = false;
      canDiscard = localActor;
      setCurrentPlayer(false);
      return;
    }

    if (type === "discard") {
      canDraw = !localActor;
      canDiscard = false;
      setCurrentPlayer(!localActor);
    }
  }

  function processAction(action, replayMode) {
    action = normaliseAction(action);

    if (!isReplayableAction(action)) {
      return;
    }

    const parts = action.split(",");
    const type = parts[0];
    const actor = parts[parts.length - 1];
    const localActor = actor === user;

    if (type === "round_complete") {
      const completedRound = Number(parts[1]);
      const winner = parts[2];

      if (
        completedRound === currentRound &&
        winner &&
        !roundComplete
      ) {
        finishRound(winner);
      }

      return;
    }

    if (type === "round_advance") {
      const completedRound = Number(parts[1]);

      if (
        completedRound !== currentRound ||
        !roundSettlement ||
        gameFinished
      ) {
        return;
      }

      if (localActor && !replayMode) {
        return;
      }

      advanceRound();
      return;
    }

    if (type === "draw") {
      let applied = false;

      if (replayMode) {
        if (localActor) {
          applied =
            parts[1] === "deck"
              ? drawPlayerFromDeck(true)
              : drawPlayerFromDiscard(true);
        } else {
          applied =
            parts[1] === "deck"
              ? drawOpponentFromDeck(true)
              : drawOpponentFromDiscard(true);
        }
      } else if (!localActor) {
        applied =
          parts[1] === "deck"
            ? drawOpponentFromDeck(true)
            : drawOpponentFromDiscard(true);
      }

      if (applied || replayMode || localActor) {
        setTurnAfterAction("draw", actor);
      }

      return;
    }

    if (type === "discard") {
      const cardParts = parts[1].split(".");
      const value = Number(cardParts[0]);
      const suit = Number(cardParts[1]);

      if (
        !Number.isInteger(value) ||
        !Number.isInteger(suit)
      ) {
        return;
      }

      if (replayMode) {
        if (localActor) {
          discardPlayerDuringReplay(value, suit);
        } else {
          discardOpponentCard(value, suit);
        }

        if (!roundSettlement) {
          setTurnAfterAction("discard", actor);
        }

        return;
      }

      if (localActor) {
        return;
      }

      if (discardOpponentCard(value, suit)) {
        if (!roundSettlement) {
          setTurnAfterAction("discard", actor);
        }
      }
    }
  }

  function rebuildFromHistory(actions) {
    const validActions = actions.filter(isReplayableAction);

    stateReceived = true;
    gameReady = false;

    currentRound = 3;
    currentCard = 0;
    deck = [];

    playerCards = [];
    playerSuits = [];
    opponentCards = [];
    opponentSuits = [];
    discardCards = [];
    discardSuits = [];

    playerScore = 0;
    opponentScore = 0;
    roundComplete = false;
    gameFinished = false;
    pendingWinner = null;
    roundKey = "";
    roundSettlement = false;
    roundWinner = null;
    settlementActionSent = false;

    dealRound(3);

    if (validActions.length === 0) {
      history = [];
      gameReady = true;
      redrawAll();
      stage.update();
      return;
    }

    validActions.forEach(function(action) {
      processAction(action, true);
    });

    history = validActions.slice();
    gameReady = true;

    if (!roundComplete && !gameFinished) {
      if (playerCards.length === currentRound) {
        canDraw = getRoundStarter(currentRound) === user;
        canDiscard = false;
      } else if (playerCards.length === currentRound + 1) {
        canDraw = false;
        canDiscard = true;
      }

      setCurrentPlayer(canDraw);
    }

    setRoundText();
    redrawAll();
    stage.update();
  }

  function receiveState(message) {
    if (
      !message ||
      message.type !== "game_state" ||
      String(message.game_id) !== gameId
    ) {
      rebuildFromHistory([]);
      return;
    }

    const actions = Array.isArray(message.history)
      ? message.history
      : [];

    rebuildFromHistory(actions);
  }

  function receiveAction(action) {
    action = normaliseAction(action);

    if (!isReplayableAction(action)) {
      return;
    }

    processAction(action, false);

    history.push(action);
    gameReady = true;
    stage.update();
  }

  function receiveMessage(text) {
    let message;

    try {
      message = JSON.parse(text);
    } catch (error) {
      if (!stateReceived) {
        rebuildFromHistory([]);
      }

      return;
    }

    if (message.type === "game_state") {
      receiveState(message);
      return;
    }

    if (
      message.type === "game_action" &&
      stateReceived
    ) {
      receiveAction(message.action);
    }
  }

  function sendAction(action) {
    if (
      !socket ||
      socket.readyState !== WebSocket.OPEN
    ) {
      return false;
    }

    socket.send(normaliseAction(action) + "/");
    return true;
  }

  function openSocket() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }

    socket = new WebSocket(
      "wss://" +
      window.location.hostname +
      "/ws/games/" +
      postUuid +
      "/" +
      gameCode +
      "/"
    );

    socket.addEventListener("open", function() {
      stateReceived = false;
      gameReady = false;
      history = [];

      sendAction("x");
    });

    socket.addEventListener("message", function(event) {
      receiveMessage(event.data);
    });

    socket.addEventListener("close", scheduleReconnect);
    socket.addEventListener("error", scheduleReconnect);
  }

  function scheduleReconnect() {
    if (reconnectTimer) {
      return;
    }

    reconnectTimer = setTimeout(function() {
      reconnectTimer = null;
      stateReceived = false;
      gameReady = false;
      history = [];
      openSocket();
    }, 5000);
  }

  /*
   * ----------------------------------------------------------------------
   * Image loading and startup
   * ----------------------------------------------------------------------
   */

  function imageLoaded() {
    imagesLoaded++;

    if (
      imagesLoaded >= 53 &&
      !started
    ) {
      started = true;
      beginGame();
    }
  }

  for (let suit = 0; suit < SUITS.length; suit++) {
    cardImages[suit] = [];

    for (let value = 0; value < CARD_NAMES.length; value++) {
      const image = new Image();

      image.onload = imageLoaded;
      image.onerror = imageLoaded;

      image.src =
        CARD_ROOT +
        CARD_NAMES[value] +
        SUITS[suit] +
        ".png";

      cardImages[suit][value] = image;
    }
  }

  backImage.onload = imageLoaded;
  backImage.onerror = imageLoaded;
  backImage.src = CARD_ROOT + "back.png";

  function beginGame() {
    drawInterface();
    resetNewGame();

    createjs.Ticker.framerate = 60;
    createjs.Ticker.addEventListener("tick", function() {
      stage.update();
    });

    gameReady = true;
    openSocket();
    stage.update();
  }
})();
