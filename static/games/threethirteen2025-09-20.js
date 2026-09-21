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
  const gameId = parseInt(gameElement.innerHTML, 10) || 0;

  const user = playerElement.innerHTML.trim() === "y"
    ? PLAYER_ONE
    : PLAYER_TWO;

  const opponent = user === PLAYER_ONE
    ? PLAYER_TWO
    : PLAYER_ONE;

  const adElement = document.getElementById("dontshowad");
  const adHeight = adElement &&
    adElement.innerHTML.trim() === "true"
    ? 0
    : 120;

  const TEXT = "bold 42px Arial";
  const LARGE_TEXT = "bold 70px Arial";
  const SMALL_TEXT = "bold 32px Arial";

  let socket = null;
  let reconnectTimer = null;

  let gameReady = false;
  let serverStateReceived = false;
  let processingHistory = false;

  let actionIndex = 0;
  let gameplay = [];

  let currentRound = 3;
  let currentCard = 0;
  let deck = [];

  let playerHandCards = [];
  let playerHandSuits = [];
  let opponentHandCards = [];
  let opponentHandSuits = [];

  let discardCards = [];
  let discardSuits = [];

  let canPlayerDraw = false;
  let canPlayerDiscard = false;

  let roundComplete = false;
  let roundCompleteKey = "";
  let gameFinished = false;
  let pendingRoundWinner = null;

  let playerScore = 0;
  let opponentScore = 0;
  let lastPlayerRoundScore = 0;
  let lastOpponentRoundScore = 0;

  let playerHandObjects = [];
  let opponentHandObjects = [];

  let discardBitmap = null;
  let previousDiscardBitmap = null;
  let deckBitmap = null;

  let wonContainer = null;
  let joinMessageContainer = null;
  let finalDialogObjects = [];

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
  let canvasSize = 0;
  const cardScale = 0.9;

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = Math.max(
      0,
      window.innerHeight - adHeight
    );

    background.graphics.clear();
    background.graphics
      .beginFill("#b0afb3")
      .drawRect(
        0,
        0,
        canvas.width,
        canvas.height
      );

    canvasSize = Math.min(
      canvas.width,
      canvas.height
    );

    if (canvasSize <= 0) {
      stage.update();
      return;
    }

    container.scaleX = canvasSize / 1000;
    container.scaleY = canvasSize / 1000;

    leftBound =
      (canvas.width - canvasSize) /
      2 /
      container.scaleX;

    topBound =
      (canvas.height - canvasSize) /
      2 /
      container.scaleY;

    stage.update();
  }

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  /*
   * ------------------------------------------------------------------------
   * Wildcard logic
   * ------------------------------------------------------------------------
   */

  function getWildcardValue() {
    return currentRound - 1;
  }

  function isWildcardValue(value) {
    return Number(value) === getWildcardValue();
  }

  function isWildcardCard(value, suit) {
    return isWildcardValue(value) &&
      Number(suit) >= 0 &&
      Number(suit) < 4;
  }

  /*
   * ------------------------------------------------------------------------
   * Deck generation
   * ------------------------------------------------------------------------
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
    return min + (this.next() % (max - min));
  };

  function makeDeck(round) {
    const cards = [];
    const rng = new RNG(
      (10000 + gameId + round * 7919) >>> 0
    );

    for (let suit = 0; suit < 4; suit++) {
      for (let value = 0; value < 13; value++) {
        cards.push({
          value: value,
          suit: suit
        });
      }
    }

    for (let i = cards.length - 1; i > 0; i--) {
      const j = rng.range(0, i + 1);
      const temp = cards[i];

      cards[i] = cards[j];
      cards[j] = temp;
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
    const combined = [];

    for (let i = 0; i < cards.length; i++) {
      combined.push({
        card: cards[i],
        suit: suits[i]
      });
    }

    combined.sort(function(a, b) {
      if (byValue && a.card !== b.card) {
        return b.card - a.card;
      }

      if (a.suit !== b.suit) {
        return b.suit - a.suit;
      }

      return b.card - a.card;
    });

    return {
      cards: combined.map(item => item.card),
      suits: combined.map(item => item.suit)
    };
  }

  function dealRound(round) {
    currentRound = round;
    deck = makeDeck(round);

    playerHandCards = [];
    playerHandSuits = [];
    opponentHandCards = [];
    opponentHandSuits = [];
    discardCards = [];
    discardSuits = [];

    for (let i = 0; i < round; i++) {
      const firstCard = getDeckCard(i);
      const secondCard = getDeckCard(round + i);

      if (user === PLAYER_ONE) {
        addCard(
          playerHandCards,
          playerHandSuits,
          firstCard
        );

        addCard(
          opponentHandCards,
          opponentHandSuits,
          secondCard
        );
      } else {
        addCard(
          opponentHandCards,
          opponentHandSuits,
          firstCard
        );

        addCard(
          playerHandCards,
          playerHandSuits,
          secondCard
        );
      }
    }

    const openingDiscard = getDeckCard(round * 2);

    if (openingDiscard) {
      discardCards.push(openingDiscard.value);
      discardSuits.push(openingDiscard.suit);
    }

    currentCard = round * 2 + 1;

    let sorted = sortCards(
      playerHandCards,
      playerHandSuits,
      true
    );

    playerHandCards = sorted.cards;
    playerHandSuits = sorted.suits;

    sorted = sortCards(
      opponentHandCards,
      opponentHandSuits,
      true
    );

    opponentHandCards = sorted.cards;
    opponentHandSuits = sorted.suits;

    roundComplete = false;
    roundCompleteKey = "";
    pendingRoundWinner = null;

    canPlayerDiscard = false;
    canPlayerDraw = getRoundStarter(round) === user;

    setCurrentPlayer(canPlayerDraw);
    setRoundText();
    redrawAll();
  }

  /*
   * ------------------------------------------------------------------------
   * Rendering
   * ------------------------------------------------------------------------
   */

  function clearObjects(objects) {
    for (const object of objects) {
      if (object && container.contains(object)) {
        container.removeChild(object);
      }
    }

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

    bitmap.scaleX = cardScale;
    bitmap.scaleY = cardScale;
    bitmap.x = leftBound + x - 125 * cardScale;
    bitmap.y = topBound + y - 175 * cardScale;

    container.addChild(bitmap);
    return bitmap;
  }

  function drawFaceDownCard(x, y) {
    const bitmap = new createjs.Bitmap(backImage);

    bitmap.scaleX = cardScale;
    bitmap.scaleY = cardScale;
    bitmap.x = leftBound + x - 125 * cardScale;
    bitmap.y = topBound + y - 175 * cardScale;

    container.addChild(bitmap);
    return bitmap;
  }

  function drawWildcardMarker(bitmap) {
    const marker = new createjs.Text(
      "WILD",
      "bold 18px Arial",
      "#7a0010"
    );

    marker.x = bitmap.x + 24;
    marker.y = bitmap.y + 22;
    marker.textAlign = "center";
    marker.mouseEnabled = false;

    container.addChild(marker);
    return marker;
  }

  function drawPlayerHand() {
    clearObjects(playerHandObjects);

    for (let i = playerHandCards.length - 1; i >= 0; i--) {
      const row = i > 6 ? 140 : 30;
      const offset = i > 6 ? 7 : 0;
      const x = 1000 - (1000 / 7) * (i - offset);
      const y = 1000 - row;

      const bitmap = drawCard(
        playerHandSuits[i],
        playerHandCards[i],
        x,
        y
      );

      if (!bitmap) {
        continue;
      }

      bitmap.card = playerHandCards[i];
      bitmap.suit = playerHandSuits[i];

      if (isWildcardCard(bitmap.card, bitmap.suit)) {
        bitmap.alpha = 0.92;
      }

      bitmap.on("mousedown", function(event) {
        if (
          !gameReady ||
          !canPlayerDiscard ||
          roundComplete ||
          playerHandCards.length !== currentRound + 1
        ) {
          return;
        }

        const value = event.currentTarget.card;
        const suit = event.currentTarget.suit;

        if (isWildcardCard(value, suit)) {
          return;
        }

        if (!discardPlayerCard(value, suit)) {
          return;
        }

        sendAction(
          "discard," +
          value +
          "." +
          suit +
          "," +
          user
        );

        if (pendingRoundWinner === user) {
          sendAction(
            "round_complete," +
            currentRound +
            "," +
            user
          );

          pendingRoundWinner = null;
        }
      });

      playerHandObjects.push(bitmap);

      if (isWildcardCard(bitmap.card, bitmap.suit)) {
        const marker = drawWildcardMarker(bitmap);
        playerHandObjects.push(marker);
      }
    }

    stage.update();
  }

  function drawOpponentHand(faceUp) {
    clearObjects(opponentHandObjects);

    for (let i = 0; i < opponentHandCards.length; i++) {
      const row = i > 6 ? 140 : 30;
      const offset = i > 6 ? 7 : 0;
      const x =
        1000 -
        (1000 / 7) *
        (i - offset + 1);

      const bitmap = faceUp
        ? drawCard(
            opponentHandSuits[i],
            opponentHandCards[i],
            x,
            row
          )
        : drawFaceDownCard(x, row);

      if (bitmap) {
        opponentHandObjects.push(bitmap);

        if (faceUp && isWildcardCard(
          opponentHandCards[i],
          opponentHandSuits[i]
        )) {
          const marker = drawWildcardMarker(bitmap);
          opponentHandObjects.push(marker);
        }
      }
    }

    stage.update();
  }

  function drawDeck() {
    if (deckBitmap && container.contains(deckBitmap)) {
      container.removeChild(deckBitmap);
    }

    deckBitmap = drawFaceDownCard(300, 500);

    deckBitmap.on("mousedown", function() {
      if (
        !gameReady ||
        !canPlayerDraw ||
        roundComplete ||
        playerHandCards.length !== currentRound
      ) {
        return;
      }

      if (drawFromDeck()) {
        sendAction("draw,deck," + user);
      }
    });
  }

  function drawDiscard() {
    if (
      previousDiscardBitmap &&
      container.contains(previousDiscardBitmap)
    ) {
      container.removeChild(previousDiscardBitmap);
    }

    previousDiscardBitmap = discardBitmap;
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

    if (isWildcardCard(
      discardCards[index],
      discardSuits[index]
    )) {
      discardBitmap.alpha = 0.94;
      const marker = drawWildcardMarker(discardBitmap);
      marker.alpha = 0.9;
    }

    discardBitmap.on("mousedown", function() {
      if (
        !gameReady ||
        !canPlayerDraw ||
        roundComplete ||
        playerHandCards.length !== currentRound
      ) {
        return;
      }

      if (drawFromDiscard()) {
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

    playerScoreText = new createjs.Text(
      "--",
      TEXT,
      "#000000"
    );

    playerScoreText.x = leftBound + 50;
    playerScoreText.y = topBound + 580;
    playerScoreText.textAlign = "center";

    opponentScoreText = new createjs.Text(
      "--",
      TEXT,
      "#000000"
    );

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

    const roundCircle = new createjs.Shape();

    roundCircle.graphics
      .beginFill("#E8CD71")
      .drawCircle(0, 0, 50);

    roundCircle.x = leftBound + 500;
    roundCircle.y = topBound + 500;

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
    container.addChild(roundCircle);
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

    const suitText = new createjs.Text(
      "333",
      TEXT,
      "#000000"
    );

    suitText.x = leftBound + 950;
    suitText.y = topBound + 380;
    suitText.textAlign = "center";

    suitButton.on("mousedown", function() {
      const sorted = sortCards(
        playerHandCards,
        playerHandSuits,
        false
      );

      playerHandCards = sorted.cards;
      playerHandSuits = sorted.suits;
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

    const valueText = new createjs.Text(
      "456",
      TEXT,
      "#000000"
    );

    valueText.x = leftBound + 950;
    valueText.y = topBound + 580;
    valueText.textAlign = "center";

    valueButton.on("mousedown", function() {
      const sorted = sortCards(
        playerHandCards,
        playerHandSuits,
        true
      );

      playerHandCards = sorted.cards;
      playerHandSuits = sorted.suits;
      drawPlayerHand();
    });

    container.addChild(suitButton);
    container.addChild(suitText);
    container.addChild(valueButton);
    container.addChild(valueText);
  }

  function setCurrentPlayer(playerMayDraw) {
    if (!currentPlayerText) {
      return;
    }

    currentPlayerText.y = playerMayDraw
      ? topBound + 670
      : topBound + 270;
  }

  function setRoundText() {
    if (!roundText) {
      return;
    }

    roundText.text =
      CARD_NAMES[currentRound - 1] ||
      String(currentRound);
  }

  /*
   * ------------------------------------------------------------------------
   * Deck and turn actions
   * ------------------------------------------------------------------------
   */

  function rebuildDiscardDeck() {
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

  function drawFromDeck() {
    if (
      !canPlayerDraw ||
      roundComplete ||
      playerHandCards.length !== currentRound
    ) {
      return false;
    }

    if (currentCard >= deck.length) {
      if (!rebuildDiscardDeck()) {
        return false;
      }
    }

    const card = getDeckCard(currentCard);

    if (!card) {
      return false;
    }

    currentCard++;
    addCard(playerHandCards, playerHandSuits, card);

    canPlayerDraw = false;
    canPlayerDiscard = true;

    drawPlayerHand();
    setCurrentPlayer(false);

    return true;
  }

  function drawFromDiscard() {
    if (
      !canPlayerDraw ||
      roundComplete ||
      playerHandCards.length !== currentRound ||
      discardCards.length === 0
    ) {
      return false;
    }

    const index = discardCards.length - 1;

    addCard(
      playerHandCards,
      playerHandSuits,
      {
        value: discardCards[index],
        suit: discardSuits[index]
      }
    );

    discardCards.pop();
    discardSuits.pop();

    canPlayerDraw = false;
    canPlayerDiscard = true;

    drawPlayerHand();
    drawDiscard();
    setCurrentPlayer(false);

    return true;
  }

  function drawOpponentFromDeck() {
    if (
      opponentHandCards.length !== currentRound
    ) {
      return false;
    }

    if (currentCard >= deck.length) {
      if (!rebuildDiscardDeck()) {
        return false;
      }
    }

    const card = getDeckCard(currentCard);

    if (!card) {
      return false;
    }

    currentCard++;
    addCard(
      opponentHandCards,
      opponentHandSuits,
      card
    );

    drawOpponentHand(false);
    return true;
  }

  function drawOpponentFromDiscard() {
    if (
      opponentHandCards.length !== currentRound ||
      discardCards.length === 0
    ) {
      return false;
    }

    const index = discardCards.length - 1;

    addCard(
      opponentHandCards,
      opponentHandSuits,
      {
        value: discardCards[index],
        suit: discardSuits[index]
      }
    );

    discardCards.pop();
    discardSuits.pop();

    drawOpponentHand(false);
    drawDiscard();
    return true;
  }

  function discardPlayerCard(value, suit) {
    if (
      !gameReady ||
      roundComplete ||
      !canPlayerDiscard ||
      playerHandCards.length !== currentRound + 1
    ) {
      return false;
    }

    if (isWildcardCard(value, suit)) {
      return false;
    }

    const index = playerHandCards.findIndex(function(card, i) {
      return (
        card === value &&
        playerHandSuits[i] === suit
      );
    });

    if (index < 0) {
      return false;
    }

    playerHandCards.splice(index, 1);
    playerHandSuits.splice(index, 1);

    discardCards.push(value);
    discardSuits.push(suit);

    canPlayerDiscard = false;
    canPlayerDraw = false;

    drawPlayerHand();
    drawDiscard();
    setCurrentPlayer(false);

    const score = calculateScore(
      playerHandCards,
      playerHandSuits
    );

    pendingRoundWinner =
      playerHandCards.length === currentRound &&
      score === 0
        ? user
        : null;

    return true;
  }

  function discardOpponentCard(value, suit) {
    if (isWildcardCard(value, suit)) {
      console.warn("Rejected wildcard discard:", value, suit);
      return false;
    }

    const index = opponentHandCards.findIndex(function(card, i) {
      return (
        card === value &&
        opponentHandSuits[i] === suit
      );
    });

    if (index < 0) {
      return false;
    }

    opponentHandCards.splice(index, 1);
    opponentHandSuits.splice(index, 1);

    discardCards.push(value);
    discardSuits.push(suit);

    drawOpponentHand(false);
    drawDiscard();

    canPlayerDraw = true;
    canPlayerDiscard = false;
    setCurrentPlayer(true);

    return true;
  }

  /*
   * ------------------------------------------------------------------------
   * Meld scoring
   * ------------------------------------------------------------------------
   */

    function calculateScore(cards, suits) {
      const counts = [];

      for (let suit = 0; suit < 4; suit++) {
        counts[suit] = [];

        for (let value = 0; value < 13; value++) {
          counts[suit][value] = 0;
        }
      }

      let wildcards = 0;

      /*
       * Card values are zero-based:
       *
       * Round 3  -> value 2  -> 3 is wild
       * Round 4  -> value 3  -> 4 is wild
       * Round 5  -> value 4  -> 5 is wild
       * ...
       * Round 13 -> value 12 -> K is wild
       */
      for (let i = 0; i < cards.length; i++) {
        if (isWildcardValue(cards[i])) {
          wildcards++;
        } else if (
          suits[i] >= 0 &&
          suits[i] < 4 &&
          cards[i] >= 0 &&
          cards[i] < 13
        ) {
          counts[suits[i]][cards[i]]++;
        }
      }

      const memo = new Map();

      function cloneCounts(source) {
        return source.map(row => row.slice());
      }

      function makeKey(state, wild) {
        return (
          wild +
          ":" +
          state.map(row => row.join("")).join("|")
        );
      }

      function cardValue(value) {
        return Math.min(value + 1, 10);
      }

      function solve(state, wild) {
        const key = makeKey(state, wild);

        if (memo.has(key)) {
          return memo.get(key);
        }

        let firstSuit = -1;
        let firstValue = -1;

        /*
         * Find the first remaining natural card.
         */
        for (let suit = 0; suit < 4; suit++) {
          for (let value = 0; value < 13; value++) {
            if (state[suit][value] > 0) {
              firstSuit = suit;
              firstValue = value;
              break;
            }
          }

          if (firstSuit !== -1) {
            break;
          }
        }

        /*
         * If there are no natural cards left, groups of three or four
         * wildcards may form complete melds. Any remainder is deadwood.
         */
        if (firstSuit === -1) {
          let best = wild * 3;

          if (wild >= 3) {
            best = Math.min(
              best,
              solve(state, wild - 3)
            );
          }

          if (wild >= 4) {
            best = Math.min(
              best,
              solve(state, wild - 4)
            );
          }

          memo.set(key, best);
          return best;
        }

        /*
         * Option 1: leave the first natural card as deadwood.
         */
        let best = cardValue(firstValue);

        /*
         * Option 2: make a set containing the first card.
         *
         * A set may contain up to four wildcards. It must contain
         * at least one natural card and have at least three cards total.
         */
        const matchingSuits = [];

        for (let suit = 0; suit < 4; suit++) {
          if (state[suit][firstValue] > 0) {
            matchingSuits.push(suit);
          }
        }

        for (
          let mask = 1;
          mask < (1 << matchingSuits.length);
          mask++
        ) {
          /*
           * The first matching suit must be included because this
           * meld must consume the first natural card.
           */
          if (!(mask & 1)) {
            continue;
          }

          const selectedSuits = [];

          for (
            let bit = 0;
            bit < matchingSuits.length;
            bit++
          ) {
            if (mask & (1 << bit)) {
              selectedSuits.push(matchingSuits[bit]);
            }
          }

          const naturalCount = selectedSuits.length;
          const neededWildcards = 3 - naturalCount;

          /*
           * A single meld may use no more than four wildcards.
           */
          if (
            neededWildcards < 0 ||
            neededWildcards > 4 ||
            neededWildcards > wild
          ) {
            continue;
          }

          const next = cloneCounts(state);

          for (const suit of selectedSuits) {
            next[suit][firstValue]--;
          }

          best = Math.min(
            best,
            solve(next, wild - neededWildcards)
          );
        }

        /*
         * Option 3: make a run containing the first card.
         *
         * A run contains natural cards of one suit in consecutive order.
         * Missing positions are supplied by wildcards.
         *
         * Up to four missing positions may be filled by wildcards.
         */
        for (let length = 3; length <= 13; length++) {
          const firstStart = Math.max(
            0,
            firstValue - length + 1
          );

          const lastStart = Math.min(
            firstValue,
            13 - length
          );

          for (
            let start = firstStart;
            start <= lastStart;
            start++
          ) {
            const end = start + length - 1;
            const next = cloneCounts(state);
            let neededWildcards = 0;

            for (
              let value = start;
              value <= end;
              value++
            ) {
              if (next[firstSuit][value] > 0) {
                next[firstSuit][value]--;
              } else {
                neededWildcards++;
              }
            }

            /*
             * This is the important limit: a single run may use
             * no more than four wildcards.
             */
            if (
              neededWildcards <= 4 &&
              neededWildcards <= wild
            ) {
              best = Math.min(
                best,
                solve(next, wild - neededWildcards)
              );
            }
          }
        }

        /*
         * Option 4: make a meld consisting entirely of wildcards.
         *
         * Three or four wildcards are both valid meld sizes for this
         * game's wildcard scoring rules.
         */
        if (wild >= 3) {
          best = Math.min(
            best,
            solve(state, wild - 3)
          );
        }

        if (wild >= 4) {
          best = Math.min(
            best,
            solve(state, wild - 4)
          );
        }

        memo.set(key, best);
        return best;
      }

      return solve(counts, wildcards);
    }

  function calculatePlayerScore() {
    return calculateScore(
      playerHandCards,
      playerHandSuits
    );
  }

  function calculateOpponentScore() {
    return calculateScore(
      opponentHandCards,
      opponentHandSuits
    );
  }

  /*
   * ------------------------------------------------------------------------
   * Round and game completion
   * ------------------------------------------------------------------------
   */

  function finishRound(winner) {
    const key = currentRound + ":" + winner;

    if (
      gameFinished ||
      roundComplete ||
      roundCompleteKey === key
    ) {
      return;
    }

    roundComplete = true;
    roundCompleteKey = key;
    canPlayerDraw = false;
    canPlayerDiscard = false;
    setCurrentPlayer(false);

    lastPlayerRoundScore = calculatePlayerScore();
    lastOpponentRoundScore = calculateOpponentScore();

    playerScore += lastPlayerRoundScore;
    opponentScore += lastOpponentRoundScore;

    drawPlayerScore(playerScore);
    drawOpponentScore(opponentScore);

    if (currentRound >= 13) {
      gameFinished = true;
      drawFinishedDialog();
      return;
    }

    drawRoundDialog(winner);
  }

  function advanceRound() {
    if (
      gameFinished ||
      !roundComplete ||
      currentRound >= 13
    ) {
      return;
    }

    removeRoundDialog();

    currentRound++;
    roundComplete = false;
    roundCompleteKey = "";
    pendingRoundWinner = null;

    dealRound(currentRound);
  }

  function drawRoundDialog(winner) {
    removeRoundDialog();

    wonContainer = new createjs.Container();

    const panel = new createjs.Shape();

    panel.graphics
      .beginFill(winner === user ? "lightgreen" : "lightblue")
      .drawRoundRect(
        leftBound + 100,
        topBound + 350,
        800,
        260,
        25
      );

    const message = new createjs.Text(
      winner === user
        ? "You won the round"
        : "Your opponent won the round",
      TEXT,
      "#000000"
    );

    message.x = leftBound + 500;
    message.y = topBound + 410;
    message.textAlign = "center";

    const hint = new createjs.Text(
      "Next round loading...",
      SMALL_TEXT,
      "#000000"
    );

    hint.x = leftBound + 500;
    hint.y = topBound + 500;
    hint.textAlign = "center";

    wonContainer.addChild(panel);
    wonContainer.addChild(message);
    wonContainer.addChild(hint);
    container.addChild(wonContainer);

    drawOpponentHand(true);
    stage.update();

    setTimeout(function() {
      if (
        roundComplete &&
        !gameFinished &&
        wonContainer &&
        container.contains(wonContainer)
      ) {
        advanceRound();
      }
    }, 1200);
  }

  function removeRoundDialog() {
    if (
      wonContainer &&
      container.contains(wonContainer)
    ) {
      container.removeChild(wonContainer);
    }

    wonContainer = null;
  }

  function drawFinishedDialog() {
    removeRoundDialog();

    for (const object of finalDialogObjects) {
      if (container.contains(object)) {
        container.removeChild(object);
      }
    }

    finalDialogObjects = [];

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

    const scoreText = new createjs.Text(
      user === PLAYER_ONE
        ? PLAYER_ONE + ": " + playerScore +
          "\n" +
          PLAYER_TWO + ": " + opponentScore
        : PLAYER_ONE + ": " + opponentScore +
          "\n" +
          PLAYER_TWO + ": " + playerScore,
      SMALL_TEXT,
      "#000000"
    );

    scoreText.x = leftBound + 500;
    scoreText.y = topBound + 520;
    scoreText.textAlign = "center";
    scoreText.lineHeight = 60;

    container.addChild(panel);
    container.addChild(title);
    container.addChild(resultText);
    container.addChild(scoreText);

    finalDialogObjects.push(
      panel,
      title,
      resultText,
      scoreText
    );

    stage.update();
    sendScore();
  }

  function sendScore() {
    if (user === PLAYER_ONE) {
      sendAction(
        "<SCORE>," +
        PLAYER_ONE +
        "," +
        playerScore +
        "," +
        opponentScore
      );
    } else {
      sendAction(
        "<SCORE>," +
        PLAYER_TWO +
        "," +
        opponentScore +
        "," +
        playerScore
      );
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
   * ------------------------------------------------------------------------
   * WebSocket protocol
   * ------------------------------------------------------------------------
   */

  function normaliseAction(action) {
    return String(action || "")
      .trim()
      .replace(/\/+$/, "");
  }

  function parseGameplay(text) {
    return String(text || "")
      .split("/")
      .map(normaliseAction)
      .filter(Boolean);
  }

  function sendAction(action) {
    if (
      !socket ||
      socket.readyState !== WebSocket.OPEN
    ) {
      console.warn(
        "Socket is not ready; action was not sent:",
        action
      );

      return false;
    }

    socket.send(normaliseAction(action) + "/");
    return true;
  }

  function processAction(action, replaying) {
    action = normaliseAction(action);

    if (!action) {
      return;
    }

    const parts = action.split(",");
    const type = parts[0];

    if (type === "join") {
      if (parts[2] && parts[2] !== user) {
        showOpponentJoined();
      }

      return;
    }

    if (type === "round_complete") {
      const completedRound = parseInt(parts[1], 10);
      const winner = parts[2];

      if (
        completedRound === currentRound &&
        winner
      ) {
        finishRound(winner);
      }

      return;
    }

    if (type === "<SCORE>") {
      return;
    }

    const actor = parts[parts.length - 1];

    if (!replaying && actor === user) {
      return;
    }

    if (type === "draw") {
      if (parts[1] === "deck") {
        drawOpponentFromDeck();
      } else if (parts[1] === "discard") {
        drawOpponentFromDiscard();
      }

      canPlayerDraw = false;
      canPlayerDiscard = false;
      setCurrentPlayer(false);

      return;
    }

    if (type === "discard") {
      const cardParts = parts[1].split(".");
      const value = parseInt(cardParts[0], 10);
      const suit = parseInt(cardParts[1], 10);

      if (
        Number.isNaN(value) ||
        Number.isNaN(suit)
      ) {
        return;
      }

      if (discardOpponentCard(value, suit)) {
        canPlayerDraw = true;
        canPlayerDiscard = false;
        setCurrentPlayer(true);
      }

      return;
    }
  }

  function rebuildFromHistory(actions) {
    processingHistory = true;
    serverStateReceived = true;

    currentRound = 3;
    currentCard = 0;
    deck = [];

    playerScore = 0;
    opponentScore = 0;
    lastPlayerRoundScore = 0;
    lastOpponentRoundScore = 0;

    gameFinished = false;
    roundComplete = false;
    roundCompleteKey = "";
    pendingRoundWinner = null;

    dealRound(3);

    for (const action of actions) {
      processAction(action, true);
    }

    gameplay = actions.slice();
    actionIndex = gameplay.length;
    processingHistory = false;
    gameReady = true;

    redrawAll();
    stage.update();
  }

  function readSocketMessage(text) {
    const incoming = parseGameplay(text);

    if (incoming.length === 0) {
      return;
    }

    if (!serverStateReceived) {
      rebuildFromHistory(incoming);
      return;
    }

    if (incoming.length === 1) {
      processAction(incoming[0], false);

      gameplay.push(incoming[0]);
      actionIndex = gameplay.length;
    } else {
      const start = Math.min(
        actionIndex,
        incoming.length
      );

      for (let i = start; i < incoming.length; i++) {
        processAction(incoming[i], false);
      }

      gameplay = incoming.slice();
      actionIndex = gameplay.length;
    }

    gameReady = true;
    stage.update();
  }

  function showOpponentJoined() {
    if (
      joinMessageContainer &&
      container.contains(joinMessageContainer)
    ) {
      return;
    }

    joinMessageContainer = new createjs.Container();

    const message = new createjs.Text(
      "Opponent joined",
      TEXT,
      "#000000"
    );

    message.x = leftBound + 500;
    message.y = topBound + 270;
    message.textAlign = "center";

    joinMessageContainer.addChild(message);
    container.addChild(joinMessageContainer);

    setTimeout(function() {
      if (
        joinMessageContainer &&
        container.contains(joinMessageContainer)
      ) {
        container.removeChild(joinMessageContainer);
      }
    }, 5000);
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
      console.log("Three-Thirteen socket open");
      sendAction("join,x," + user);
    });

    socket.addEventListener("message", function(event) {
      readSocketMessage(event.data);
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
      serverStateReceived = false;
      actionIndex = 0;
      gameplay = [];
      openSocket();
    }, 5000);
  }

  /*
   * ------------------------------------------------------------------------
   * Confetti
   * ------------------------------------------------------------------------
   */

  const cardImages = [];
  const backImage = new Image();

  const confetti = [];
  const confettiVelocityX = [];
  const confettiVelocityY = [];
  const confettiColors = [
    "Red",
    "Orange",
    "Yellow",
    "Green",
    "Blue",
    "Purple"
  ];

  const confettiCount = 60;
  let confettiActive = false;
  let imagesLoaded = 0;
  let beginStarted = false;

  function imageLoaded() {
    imagesLoaded++;

    if (
      imagesLoaded >= 53 &&
      !beginStarted
    ) {
      beginStarted = true;
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

  function setupConfetti() {
    for (let i = 0; i < confettiCount; i++) {
      const piece = new createjs.Shape();

      piece.graphics
        .beginFill(
          confettiColors[
            i % confettiColors.length
          ]
        )
        .drawCircle(0, 0, 8);

      piece.visible = false;
      confetti.push(piece);
      confettiVelocityX.push(0);
      confettiVelocityY.push(0);
      stage.addChild(piece);
    }
  }

  function dropConfetti() {
    confettiActive = true;

    for (let i = 0; i < confetti.length; i++) {
      confetti[i].visible = true;
      confetti[i].x = Math.random() * canvas.width;
      confetti[i].y = -Math.random() * 600;
      confettiVelocityX[i] =
        (Math.random() - 0.5) * 2;
      confettiVelocityY[i] =
        Math.random() * 4 + 2;
    }
  }

  function tickConfetti() {
    if (!confettiActive) {
      return;
    }

    let active = false;

    for (let i = 0; i < confetti.length; i++) {
      if (!confetti[i].visible) {
        continue;
      }

      confetti[i].x += confettiVelocityX[i];
      confetti[i].y += confettiVelocityY[i];

      if (confetti[i].y < canvas.height + 30) {
        active = true;
      } else {
        confetti[i].visible = false;
      }
    }

    confettiActive = active;
  }

  function beginGame() {
    drawInterface();
    setupConfetti();
    dealRound(3);

    createjs.Ticker.framerate = 60;

    createjs.Ticker.addEventListener("tick", function() {
      tickConfetti();
      stage.update();
    });

    gameReady = true;
    openSocket();
    stage.update();
  }
})();
