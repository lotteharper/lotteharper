(function threeThirteenGame() {
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

  /*
   * ----------------------------------------------------------------------
   * Card object model
   * ----------------------------------------------------------------------
   */

  function Card(value, suit) {
    this.value = Number(value);
    this.suit = Number(suit);
  }

  Card.prototype.getValue = function() {
    return this.value;
  };

  Card.prototype.getSuit = function() {
    return this.suit;
  };

  Card.prototype.clone = function() {
    return new Card(this.value, this.suit);
  };

  function cloneMatrix(matrix) {
    const copy = [];

    for (let i = 0; i < matrix.length; i++) {
      copy[i] = matrix[i].slice();
    }

    return copy;
  }

  function roundWildcardValue(roundNumber) {
    return Number(roundNumber || currentRound || 3) - 1;
  }

  function isWildcardCard(card, roundNumber) {
    if (!card || typeof card.getValue !== "function") {
      return false;
    }

    const wildcardValue = roundWildcardValue(roundNumber);

    return Number(card.getValue()) === wildcardValue;
  }

  /*
   * ----------------------------------------------------------------------
   * Scoring helper, based on the original hand object design
   * ----------------------------------------------------------------------
   */

  function Hand(cards, jokers, roundNumber) {
    this.roundNumber = Number(roundNumber || currentRound || 3);
    this.cards = cloneMatrix(cards);
    this.jokers = Number(jokers || 0);
    this.melds = [];
    this.value = this.leftoverValue();
  }

  Hand.prototype.findMelds = function(startSuit, startNumber) {
    if (
      typeof startSuit === "undefined" ||
      typeof startNumber === "undefined"
    ) {
      startSuit = 0;
      startNumber = 0;
      this.value = this.leftoverValue();
    }

    if (this.jokers > 2) {
      for (let i = 0; i < this.jokers; i++) {
        this.melds.push({ s: -1, n: -1 });
      }

      this.value -= this.roundNumber * this.jokers;
    }

    while (this.value > 0) {
      while (
        startNumber > 15 ||
        !this.cards[startSuit] ||
        this.cards[startSuit][startNumber] === 0
      ) {
        startNumber++;

        if (startNumber > 15) {
          startNumber = 0;
          startSuit++;

          if (startSuit > 3) {
            return;
          }
        }
      }

      for (let meldType = 0; meldType < 2; meldType++) {
        const meld = meldType
          ? this.findSet(startSuit, startNumber)
          : this.findRun(startSuit, startNumber);

        for (let length = 3; length <= meld.length; length++) {
          const test = new Hand(
            this.cards,
            this.jokers,
            this.roundNumber
          );

          test.removeCards(meld.slice(0, length));

          if (meldType) {
            test.findMelds(startSuit, startNumber);
          } else {
            test.findMelds(0, 0);
          }

          if (test.value < this.value) {
            this.value = test.value;
            this.melds.length = 0;
            this.melds = [].concat(
              meld.slice(0, length),
              test.melds
            );
          }
        }
      }

      startNumber++;
    }
  };

  Hand.prototype.findRun = function(suit, number) {
    const run = [];
    let jokers = this.jokers;

    while (number < 14) {
      if (
        (number === 13 && this.cards[suit][0] > 0) ||
        (number < 13 && this.cards[suit][number] > 0)
      ) {
        run.push({ s: suit, n: number });
      } else if (jokers > 0) {
        run.push({ s: -1, n: -1 });
        jokers--;
      } else {
        break;
      }

      number++;
    }

    while (jokers-- > 0) {
      run.push({ s: -1, n: -1 });
    }

    return run;
  };

  Hand.prototype.findSet = function(suit, number) {
    const set = [];

    for (let currentSuit = suit; currentSuit < 4; currentSuit++) {
      const count = this.cards[currentSuit][number] || 0;

      for (let i = 0; i < count; i++) {
        set.push({ s: currentSuit, n: number });
      }
    }

    for (let i = 0; i < this.jokers; i++) {
      set.push({ s: -1, n: -1 });
    }

    return set;
  };

  Hand.prototype.removeCards = function(cards) {
    for (let i = 0; i < cards.length; i++) {
      const card = cards[i];

      if (card.s >= 0 && card.n < 13) {
        this.cards[card.s][card.n]--;
      } else if (card.s >= 0 && card.n === 13) {
        this.cards[card.s][0]--;
      } else {
        this.jokers--;
      }
    }

    this.value = this.leftoverValue();
  };

  Hand.prototype.leftoverValue = function() {
    let leftover = 0;

    for (let suit = 0; suit < 4; suit++) {
      for (let number = 0; number < 13; number++) {
        let value = number + 1;

        if (value > 10) {
          value = 10;
        }

        leftover += this.cards[suit][number] * value;
      }
    }

    leftover += this.jokers * this.roundNumber;

    return leftover;
  };

  function buildMatrixFromCards(cards, roundNumber) {
    const matrix = [];

    for (let suit = 0; suit < 4; suit++) {
      matrix[suit] = [];

      for (let value = 0; value < 13; value++) {
        matrix[suit][value] = 0;
      }
    }

    let jokers = 0;

    for (let i = 0; i < cards.length; i++) {
      const card = cards[i];

      if (!card || typeof card.getValue !== "function") {
        continue;
      }

      if (isWildcardCard(card, roundNumber)) {
        jokers++;
        continue;
      }

      const suit = Number(card.getSuit());
      const value = Number(card.getValue());

      if (
        Number.isInteger(suit) &&
        suit >= 0 &&
        suit < 4 &&
        Number.isInteger(value) &&
        value >= 0 &&
        value < 13
      ) {
        matrix[suit][value]++;
      }
    }

    return { matrix, jokers };
  }

  function calculateScore(cards, roundNumber) {
    const round = Number(roundNumber || globalCurrentRound || 3);

    const { matrix, jokers } = buildMatrixFromCards(cards, round);

    const hand = new Hand(matrix, jokers, round);
    hand.findMelds();

    return hand.value;
  }

  /*
   * ----------------------------------------------------------------------
   * Deterministic shuffle
   * ----------------------------------------------------------------------
   */

  function hashSeed(value) {
    const text = String(value);

    let hash = 2166136261;

    for (let i = 0; i < text.length; i++) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }

    return hash >>> 0;
  }

  function createSeededRandom(seed) {
    let state = seed >>> 0;

    return function() {
      state = (state + 0x6D2B79F5) >>> 0;

      let value = state;
      value = Math.imul(value ^ (value >>> 15), value | 1);
      value ^= value + Math.imul(value ^ (value >>> 7), value | 61);

      return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
    };
  }

  function getDeckSeed(roundNumber) {
    return hashSeed(
      "three-thirteen:" +
      String(gameId) +
      ":round:" +
      String(Number(roundNumber))
    );
  }

  function createDeck(roundNumber) {
    const round = Number(roundNumber);

    if (
      !Number.isInteger(round) ||
      round < 3 ||
      round > 13
    ) {
      throw new RangeError(
        "Three Thirteen round must be between 3 and 13."
      );
    }

    const cards = [];

    for (let suit = 0; suit < 4; suit++) {
      for (let value = 0; value < 13; value++) {
        cards.push(new Card(value, suit));
      }
    }

    const random = createSeededRandom(
      getDeckSeed(round)
    );

    for (let i = cards.length - 1; i > 0; i--) {
      const j = Math.floor(random() * (i + 1));

      const temp = cards[i];
      cards[i] = cards[j];
      cards[j] = temp;
    }

    return cards;
  }

  /*
   * ----------------------------------------------------------------------
   * Game state
   * ----------------------------------------------------------------------
   */

  let currentRound = 3;
  let globalCurrentRound = 3;

  function getRoundStarter(roundNumber) {
    return Number(roundNumber || currentRound) % 2 === 1
      ? PLAYER_ONE
      : PLAYER_TWO;
  }

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

  const cardImages = [];
  const backImage = new Image();
  let imagesLoaded = 0;
  let started = false;

  let socket = null;
  let reconnectTimer = null;

  let stateReceived = false;
  let gameReady = false;

  let playerCards = [];
  let playerSuits = [];
  let opponentCards = [];
  let opponentSuits = [];
  let discardCards = [];
  let discardSuits = [];

  let deck = [];
  let currentCard = 0;

  let canDraw = false;
  let canDiscard = false;
  let roundComplete = false;
  let gameFinished = false;
  let pendingWinner = null;
  let roundKey = "";
  let roundScoreApplied = false;

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

  function dealRound(roundNumber) {
    globalCurrentRound = Number(roundNumber || 3);
    currentRound = globalCurrentRound;

    /*
     * This is the key fix: every round is shuffled deterministically
     * from the shared game ID and round number, so both players
     * get the same starting deck order.
     */
    deck = createDeck(currentRound);

    playerCards = [];
    playerSuits = [];
    opponentCards = [];
    opponentSuits = [];
    discardCards = [];
    discardSuits = [];

    for (let i = 0; i < currentRound; i++) {
      const first = deck.shift().clone();
      const second = deck.shift().clone();

      if (user === PLAYER_ONE) {
        playerCards.push(first);
        opponentCards.push(second);
      } else {
        opponentCards.push(first);
        playerCards.push(second);
      }
    }

    if (deck.length > 0) {
      const openingDiscard = deck.shift().clone();
      discardCards.push(openingDiscard);
      discardSuits.push(openingDiscard.getSuit());
    }

    currentCard = 0;

    roundComplete = false;
    roundKey = "";
    pendingWinner = null;
    roundScoreApplied = false;

    canDiscard = false;
    canDraw = getRoundStarter(currentRound) === user;

    setRoundText();
    setCurrentPlayer(canDraw);
    redrawAll();
  }

  function resetNewGame() {
    currentRound = 3;
    globalCurrentRound = 3;

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
    roundScoreApplied = false;

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
    const cardIndex = Number(value);
    const suitIndex = Number(suit);

    if (
      !cardImages[suitIndex] ||
      !cardImages[suitIndex][cardIndex]
    ) {
      return null;
    }

    const bitmap = new createjs.Bitmap(
      cardImages[suitIndex][cardIndex]
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

      const card = playerCards[i];

      if (!card) {
        continue;
      }

      const bitmap = drawCard(
        card.getSuit(),
        card.getValue(),
        x,
        y
      );

      if (!bitmap) {
        continue;
      }

      bitmap.cardValue = card.getValue();
      bitmap.cardSuit = card.getSuit();
      playerObjects.push(bitmap);

      if (isWildcardCard(card, currentRound)) {
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

        const value = event.currentTarget.cardValue;
        const suit = event.currentTarget.cardSuit;

        if (isWildcardCard(new Card(value, suit), currentRound)) {
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
          roundSettlement &&
          roundWinner !== user
        ) {
          completeSettlementTurn();
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

      const card = opponentCards[i];

      if (!card) {
        continue;
      }

      const bitmap = faceUp
        ? drawCard(
            card.getSuit(),
            card.getValue(),
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
        isWildcardCard(card, currentRound)
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

    const topCard = discardCards[discardCards.length - 1];

    if (!topCard) {
      stage.update();
      return;
    }

    discardBitmap = drawCard(
      topCard.getSuit(),
      topCard.getValue(),
      700,
      500
    );

    if (!discardBitmap) {
      return;
    }

    if (isWildcardCard(topCard, currentRound)) {
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
      const sorted = sortPlayerCards();
      playerCards = sorted;
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
      const sorted = sortPlayerCards(true);
      playerCards = sorted;
      drawPlayerHand();
    });

    container.addChild(suitButton);
    container.addChild(suitText);
    container.addChild(valueButton);
    container.addChild(valueText);
  }

  function sortPlayerCards(byValue) {
    return playerCards.slice().sort(function(a, b) {
      if (byValue && a.getValue() !== b.getValue()) {
        return b.getValue() - a.getValue();
      }

      if (a.getSuit() !== b.getSuit()) {
        return a.getSuit() - b.getSuit();
      }

      return b.getValue() - a.getValue();
    });
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
   * Turn functions
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

    const topCard = discardCards[discardCards.length - 1];
    const recycled = [];

    for (let i = 0; i < discardCards.length - 1; i++) {
      recycled.push(discardCards[i].clone());
    }

    deck = recycled.slice();
    currentCard = 0;

    discardCards = [topCard.clone()];
    discardSuits = [topCard.getSuit()];

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

    const card = deck[currentCard];

    if (!card) {
      return false;
    }

    currentCard++;
    playerCards.push(card.clone());

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

    const topCard = discardCards[discardCards.length - 1];

    if (!topCard) {
      return false;
    }

    playerCards.push(topCard.clone());

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

    const card = deck[currentCard];

    if (!card) {
      return false;
    }

    currentCard++;
    opponentCards.push(card.clone());

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

    const topCard = discardCards[discardCards.length - 1];

    if (!topCard) {
      return false;
    }

    opponentCards.push(topCard.clone());

    discardCards.pop();
    discardSuits.pop();

    if (!replayMode) {
      setTurnAfterAction("draw", opponent);
    }

    drawOpponentHand(false);
    drawDiscard();

    return true;
  }

  function scoreCompletedRound() {
    if (roundScoreApplied) {
      return false;
    }

    playerScore += calculateScore(
      playerCards,
      currentRound
    );

    opponentScore += calculateScore(
      opponentCards,
      currentRound
    );

    roundScoreApplied = true;

    drawPlayerScore(playerScore);
    drawOpponentScore(opponentScore);

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

    if (!scoreCompletedRound()) {
      return false;
    }

    settlementActionSent = true;

    if (currentRound >= 13) {
      gameFinished = true;
      roundSettlement = false;
      roundComplete = true;
      canDraw = false;
      canDiscard = false;

      drawFinishedDialog();
      stage.update();
      return true;
    }

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

    const match = playerCards.findIndex(function(card) {
      return (
        Number(card.getValue()) === Number(value) &&
        Number(card.getSuit()) === Number(suit)
      );
    });

    if (match < 0) {
      return false;
    }

    const card = playerCards.splice(match, 1)[0];
    discardCards.push(card.clone());
    discardSuits.push(card.getSuit());

    canDraw = false;
    canDiscard = false;

    drawPlayerHand();
    drawDiscard();

    if (roundSettlement) {
      return true;
    }

    setCurrentPlayer(false);

    pendingWinner =
      playerCards.length === currentRound &&
      calculateScore(playerCards, currentRound) === 0
        ? user
        : null;

    return true;
  }

  function discardPlayerDuringReplay(value, suit) {
    const match = playerCards.findIndex(function(card) {
      return (
        Number(card.getValue()) === Number(value) &&
        Number(card.getSuit()) === Number(suit)
      );
    });

    if (match < 0) {
      return false;
    }

    const card = playerCards.splice(match, 1)[0];
    discardCards.push(card.clone());
    discardSuits.push(card.getSuit());

    drawPlayerHand();
    drawDiscard();
    return true;
  }

  function discardOpponentCard(value, suit) {
    const match = opponentCards.findIndex(function(card) {
      return (
        Number(card.getValue()) === Number(value) &&
        Number(card.getSuit()) === Number(suit)
      );
    });

    if (match < 0) {
      return false;
    }

    const card = opponentCards.splice(match, 1)[0];
    discardCards.push(card.clone());
    discardSuits.push(card.getSuit());

    drawOpponentHand(false);
    drawDiscard();
    return true;
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
    roundScoreApplied = false;

    canDraw = winner !== user;
    canDiscard = false;

    showRoundSettlementDialog(winner);
    setCurrentPlayer(canDraw);
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
    globalCurrentRound = nextRound;
    currentCard = 0;

    roundSettlement = false;
    roundWinner = null;
    settlementActionSent = false;
    roundScoreApplied = false;
    roundComplete = false;
    roundKey = "";
    pendingWinner = null;

    canDraw = getRoundStarter(currentRound) === user;
    canDiscard = false;

    dealRound(nextRound);

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

      if (!roundScoreApplied) {
        scoreCompletedRound();
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
    globalCurrentRound = 3;
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
    roundScoreApplied = false;

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
   * Startup
   * ----------------------------------------------------------------------
   */

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
