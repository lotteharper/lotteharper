// By Charlotte Grace Harper. V1.0.33 fixing - REVISED
(function threethirteen(){
  var gameSocket;
  var gameReady = false;
  const TURNTIME = 5; // Turn time in seconds
  var currentTurn = 0;
  var lastPlayerScore = 0;
  var lastOpponentScore = 0;
  const suitnames = ["S", "H", "C", "D"];
  const cardnames = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"];
  const cardsroot = "https://lotteh.com/media/games/cards/";
  
  try {
    var postUuid = document.getElementById("post_id").innerHTML;
    var gameCode = document.getElementById("game_code").innerHTML;
  } catch { return; }
  
  var player2;
  var user;
  var preparingForNextRound = false;
  let isFinished = false;
  var gameIsWon = false;
  var opponentWinsOnNextDiscard = false;
  var gameOverOnNextDiscard = false;
  var recoveringState = false;
  
  function docReady(fn) {
    if (document.readyState === "complete" || document.readyState === "interactive") {
      setTimeout(fn, 1);
    } else {
      document.addEventListener("DOMContentLoaded", fn);
    }
  }
  
  var startedGame = false;
  var gameSocketReloadTimeout;
  
  function openGameSocket() {
    gameSocket = new WebSocket("wss://" + window.location.hostname + '/ws/games/' + postUuid + '/' + gameCode + '/');
    gameSocket.addEventListener("open", (event) => {
      console.log('Socket open.');
      send("join,x,"+user);
    });
    gameSocket.addEventListener("message", (event) => {
      read(event.data);
    });
    gameSocket.addEventListener("close", (event) => {
      console.log('Socket closed.');
      if(gameSocketReloadTimeout) clearTimeout(gameSocketReloadTimeout);
      gameSocketReloadTimeout = setTimeout(function() {
        openGameSocket();
      }, 10000);
    });
    gameSocket.addEventListener("error", (event) => {
      console.log('Socket error.');
      if(gameSocketReloadTimeout) clearTimeout(gameSocketReloadTimeout);
      gameSocketReloadTimeout = setTimeout(function() {
        openGameSocket();
      }, 10000);
    });
  }
  
  setTimeout(function() {
    openGameSocket();
  }, 5000);
  
  let seed = 10000 + parseInt(document.getElementById('game_id').innerHTML);
  
  function RNG(seed) {
    this.m = 0x80000000;
    this.a = 1103515245;
    this.c = 12345;
    this.state = seed ? seed : Math.floor(Math.random() * (this.m - 1));
  }
  
  RNG.prototype.nextInt = function() {
    this.state = (this.a * this.state + this.c) % this.m;
    return this.state;
  }
  
  RNG.prototype.nextFloat = function() {
    return this.nextInt() / (this.m - 1);
  }
  
  RNG.prototype.nextRange = function(start, end) {
    let rangeSize = end - start;
    let randomUnder1 = this.nextInt() / this.m;
    return start + Math.floor(randomUnder1 * rangeSize);
  }
  
  RNG.prototype.choice = function(array) {
    return array[this.nextRange(0, array.length)];
  }
  
  let rng = new RNG(seed);
  let canvasid = "game";
  let canvas = document.getElementById(canvasid);
  let width = canvas.width;
  let height = canvas.height;

  let TEXTTYPE = "bold " + 42 + "px Arial";
  let TEXTTYPE2 = "bold " + 70 + "px Arial";
  let TEXTTYPE3 = "bold " + 40 + "px Arial";

  let last = 0;
  let stage = new createjs.Stage(canvasid);
  let container = new createjs.Container();

  background = new createjs.Shape();
  background.graphics.beginFill("#b0afb3").drawRect(0, 0, window.innerWidth, window.innerHeight);
  stage.addChild(background);
  stage.addChild(container);

  var dontshowad;
  try {
    dontshowad = document.getElementById("dontshowad").innerHTML;
  } catch { }
  
  var ADHEIGHT = 120;
  if(dontshowad == "true"){
    ADHEIGHT = 0;
  }
  
  var totalScore = 0;
  let id;
  var player1;
  let canvasHeight;
  
  try {
    id = document.getElementById("game_id").innerHTML;
    player = document.getElementById("player").innerHTML;
    player1 = 'Player 1';
    player2 = 'Player 2';
    user = 'Player 2';
    var canPlayerDraw = false;
    if(player == 'y') {
      user = 'Player 1';
    }
    rng = new RNG(parseInt(id));
    stage.canvas.width = window.innerWidth;
    canvasHeight = window.innerHeight-ADHEIGHT;
    stage.canvas.height = canvasHeight;
  } catch {
    stage.canvas.height = 0;
  }
  
  var canPlayerDiscard = false;
  if(user == player2){
    canPlayerDraw = false;
  }
  
  let less = window.innerWidth;
  if(canvasHeight < less){
    less = canvasHeight;
  }
  scale = container.scale = less / 1000;

  leftbound = (stage.canvas.width - less)/2/scale;
  topbound = ((canvasHeight - less)/2)/scale;

  var cardScale = 0.9;
  var cardCount = 53;
  var suits = ["S","H","C","D"]
  var cards = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
  var images = []
  
  for(var x = 0; x < suits.length; x++){
    suit = suits[x];
    images[x] = []
    for(var y = 0; y < cards.length; y++){
      card = cards[y];
      images[x][y] = new Image();
      images[x][y].src = cardsroot + card + suit + ".png";
      images[x][y].onload = handleImageLoad;
    }
  }

  var backImage = new Image();
  backImage.src = cardsroot + "back.png";
  backImage.onload = handleImageLoad;
  var imageCount = 0;
  
  function handleImageLoad(event) {
    imageCount++;
    if(imageCount == cardCount){
      beginGame();
    }
  }

  function drawCard(suit,card,x,y){
    var bitmap = new createjs.Bitmap(images[suit][card]);
    bitmap.scale = cardScale;
    bitmap.x = leftbound + x-250 * cardScale/2;
    bitmap.y = topbound + y-350 * cardScale/2;
    container.addChild(bitmap);
    stage.update();
    return bitmap
  }

  var playerHandCards = [];
  var playerHandSuits = [];
  var opponentHandCards = [];
  var opponentHandSuits = [];

  var yo1 = 140;
  var yo2 = 30;

  var opponentHandCount = 0;
  var opponentHandObjects = []
  
  function drawOpponentHand(){
    opponentHandCount = 0;
    // FIXED: Safely remove all opponent hand objects
    for(var i = 0; i < opponentHandObjects.length; i++){
      try {
        if(opponentHandObjects[i] && container.contains(opponentHandObjects[i])){
          container.removeChild(opponentHandObjects[i]);
        }
      } catch(e) {
        console.log("Error removing opponent card: " + e);
      }
    }
    opponentHandObjects = []
    
    for(var i = currentRound - 1; i >= 0; i--){
      yoffset = yo2;
      ioffset = 0;
      if(i > 6){
        yoffset = yo1;
        ioffset = 7;
      }
      opponentHandObjects[opponentHandCount] = drawFacedownCard(1000-(1000/7 * (i-ioffset)), yoffset);
      opponentHandCount++;
    }
  }

  function drawFacedownCard(x,y){
    var bitmap = new createjs.Bitmap(backImage);
    bitmap.scale = cardScale;
    bitmap.x = leftbound + x-250 * cardScale/2;
    bitmap.y = topbound + y - 350 * cardScale/2;
    container.addChild(bitmap);
    stage.update();
    return bitmap;
  }

  var playerHandCount = 0;
  var playerHandObjects = []

  var currentRound = 3;
  const nsuits = [0, 1, 2, 3];
  const values = [0,1,2,3,4,5,6,7,8,9,10,11,12];

  var deck = [];

  function createAndShuffleDeck(){
    deck = [];
    for (let i = 0; i < nsuits.length; i++) {
      for (let x = 0; x < values.length; x++) {
        let card = { Value: values[x], Suit: nsuits[i] };
        deck.push(card);
      }
    }
    for (let i = deck.length - 1; i > 0; i--) {
      let j = Math.floor(rng.nextFloat() * i);
      let temp = deck[i];
      deck[i] = deck[j];
      deck[j] = temp;
    }
  }

  createAndShuffleDeck();

  opponentHandCards = []
  opponentHandSuits = []
  playerHandCards = []
  playerHandSuits = []
  
  var deckCount = currentRound*2+1
  var firstdiscard = deck[currentRound*2 + 1].Value
  var firstdiscardsuit = deck[currentRound*2 + 1].Suit
  
  if(user == player1){
    for (let i = 0; i < currentRound; i++) {
      playerHandCards[i] = deck[i].Value
      playerHandSuits[i] = deck[i].Suit
    }
    for (let i = currentRound; i < currentRound*2; i++) {
      opponentHandCards[i-currentRound] = deck[i].Value
      opponentHandSuits[i-currentRound] = deck[i].Suit
    }
  } else {
    for (let i = 0; i < currentRound; i++) {
      opponentHandCards[i] = deck[i].Value
      opponentHandSuits[i] = deck[i].Suit
    }
    for (let i = currentRound; i < currentRound*2; i++) {
      playerHandCards[i-currentRound] = deck[i].Value
      playerHandSuits[i-currentRound] = deck[i].Suit
    }
  }

  var discardcard = [firstdiscard]
  var discardsuit = [firstdiscardsuit]

  function drawOpponentHandFaceup(){
    sortOpponentHand(false);
    sortOpponentHand(true);
    opponentHandCount = 0;
    // FIXED: Safely remove all opponent hand objects
    for(var i = 0; i < opponentHandObjects.length; i++){
      try {
        if(opponentHandObjects[i] && container.contains(opponentHandObjects[i])){
          container.removeChild(opponentHandObjects[i]);
        }
      } catch(e) {
        console.log("Error removing opponent card: " + e);
      }
    }
    opponentHandObjects = []
    
    for(var i = 0; i < opponentHandCards.length; i++){
      yoffset = yo2;
      ioffset = 0;
      if(i > 6){
        yoffset = yo1;
        ioffset = 7;
      }
      opponentHandObjects[opponentHandCount] = drawCard(opponentHandSuits[i],opponentHandCards[i],1000-(1000/7 * (i-ioffset+1)), yoffset);
      if(i > 6){
        container.setChildIndex(opponentHandObjects[opponentHandCount], container.getNumChildren()-12);
      }
      opponentHandCount++;
    }
  }
  
  function playerDiscard(card, suit){
    console.log("canPlayerDiscard: " + canPlayerDiscard);
    if(card + 1 != currentRound && playerHandCards.length > currentRound) {
      canPlayerDiscard = false;
      canPlayerDraw = false;
      nCards = []
      nSuits = []
      var count = 0;
      var first = true;
      for(var x = 0; x < playerHandCards.length; x++){
        if(!(suit == playerHandSuits[x] && card == playerHandCards[x]) && first){
          nCards[count] = playerHandCards[x]
          nSuits[count] = playerHandSuits[x]
          count++;
        } else if(!first) {
          nCards[count] = playerHandCards[x]
          nSuits[count] = playerHandSuits[x]
          count++;
        } else {
          first = false;
        }
      }
      discardcard[discardcard.length] = card
      discardsuit[discardsuit.length] = suit
      playerHandCards = nCards
      playerHandSuits = nSuits
      drawDiscard();
      drawHand();
      checkOpponentWin();
      canPlayerDraw = true;
      canPlayerDiscard = false;
      
      if(opponentWinsOnNextDiscard){
        opponentWonGame();
      } else {
        canPlayerDiscard = false;
        canPlayerDraw = false;
      }
      setCurrentPlayer(false);
      currentTurn = currentTurn + 1;
    }
  }

  function drawHand(){
    canPlayerDiscard = false;
    var playerHandCount = 0;
    // FIXED: Safely remove all player hand objects
    for(var i = 0; i < playerHandObjects.length; i++){
      try {
        if(playerHandObjects[i] && container.contains(playerHandObjects[i])){
          container.removeChild(playerHandObjects[i]);
        }
      } catch(e) {
        console.log("Error removing player card: " + e);
      }
    }
    playerHandObjects = []
    
    for(var i = playerHandCards.length-1; i >= 0; i--){
      yoffset = yo2;
      ioffset = 0;
      if(i > 6){
        yoffset = yo1;
        ioffset = 7;
      }
      playerHandObjects[playerHandCount] = drawCard(playerHandSuits[i],playerHandCards[i],1000-(1000/7 * (i-ioffset)), 1000-yoffset);
      playerHandObjects[playerHandCount].suit = playerHandSuits[i]
      playerHandObjects[playerHandCount].card = playerHandCards[i]
      playerHandObjects[playerHandCount].on("mousedown", function(event) {
        var allAlike = true;
        var lastObject = playerHandObjects[0];
        for(object of playerHandObjects) {
          if(object.card != lastObject.card) allAlike = false;
          lastObject = object;
        }
        if(gameReady && playerHandCards.length > currentRound && (event.target.card != playerHandObjects.length - 2 || (allAlike && event.target.card == playerHandObjects.length - 2))){
          playerDiscard(event.target.card, event.target.suit);
          send("discard," + event.target.card + "." + event.target.suit + "," + user)
        }
      });
      playerHandCount++;
    }
  }

  var playerSorted = false;

  function sortHand(numberOrSuit){
    playerSorted = numberOrSuit;
    if(!numberOrSuit){
      sortHand(true);
    }
    var list = [];
    for (var j = 0; j < playerHandCards.length; j++)
      list.push({'card': playerHandCards[j], 'suit': playerHandSuits[j]});
    
    if(numberOrSuit){
      list.sort(function(a, b) {
        return ((a.card > b.card) ? -1 : ((a.card == b.card) ? 0 : 1));
      });
    } else {
      list.sort(function(a, b) {
        return ((a.suit > b.suit) ? -1 : ((a.suit == b.suit) ? 0 : 1));
      });
    }

    for (var k = 0; k < list.length; k++) {
      playerHandCards[k] = list[k].card;
      playerHandSuits[k] = list[k].suit;
    }
  }

  function sortOpponentHand(numberOrSuit){
    if(!numberOrSuit){
      sortOpponentHand(true);
    }
    var list = [];
    for (var j = 0; j < opponentHandCards.length; j++)
      list.push({'card': opponentHandCards[j], 'suit': opponentHandSuits[j]});
    
    if(numberOrSuit){
      list.sort(function(a, b) {
        return ((a.card > b.card) ? -1 : ((a.card == b.card) ? 0 : 1));
      });
    } else {
      list.sort(function(a, b) {
        return ((a.suit > b.suit) ? -1 : ((a.suit == b.suit) ? 0 : 1));
      });
    }

    for (var k = 0; k < list.length; k++) {
      opponentHandCards[k] = list[k].card;
      opponentHandSuits[k] = list[k].suit;
    }
  }

  function Card(valueInput, suitInput) {
    var suit = suitInput;
    var value = Number(valueInput);
    var counted = true;
    var scoringMode = "";
    var ignored = false;

    this.getSuit = function() {return suit};
    this.setSuit = function(s) {suit = s};
    this.getValue = function() {return value};
    this.setValue = function(v) {value = Number(v)};
    this.isCounted = function() {return counted};
    this.setCounted = function(cnt) {counted = cnt};
    this.getScoringMode = function() {return scoringMode};
    this.setScoringMode = function(s) {scoringMode = s};
    this.ignored = function() {return ignored};
    this.setIgnored = function(i) {ignored = i};
  }

  var allCardsPlayed;

  function isWildcard(value){
    return value.getValue() == currentRound-1
  }

  function Hand(cards, jokers) {
    this.cards = clone(cards);
    this.jokers = jokers;
    this.melds = [];
    this.value = this.leftoverValue();
  }

  Hand.prototype.findMelds = function(suit, number) {
    if (suit == undefined || number == undefined) {
      suit = number = 0;
      this.value = this.leftoverValue();
    }

    if (this.jokers > 2) {
      for (var i = 0; i < this.jokers; i++) {
        this.melds.push({s:-1, n:-1});
      }
      this.value -= currentRound * this.jokers
    }

    while (this.value > 0) {
      while (number > 15 || this.cards[suit][number] == 0) {
        if (++number > 15) {
          number = 0;
          if (++suit > 3) return;
        }
      }
      for (var meldType = 0; meldType < 2; meldType++) {
        var meld = meldType ? this.findSet(suit, number) : this.findRun(suit, number);

        for (var len = 3; len <= meld.length; len++) {
          var test = new Hand(this.cards, this.jokers);
          test.removeCards(meld.slice(0, len));

          meldType ? test.findMelds(suit, number) : test.findMelds(0, 0);

          if (test.value < this.value) {
            this.value = test.value;
            this.melds.length = 0;
            this.melds = [].concat(meld.slice(0, len), test.melds);
          }
        }
      }
      number++;
    }
  }

  Hand.prototype.findRun = function(s, n) {
    var run = [], jokers = this.jokers;
    while (n < 14) {
      if ((n == 13 && this.cards[s][0] > 0) || this.cards[s][n] > 0) {
        run.push({s:s, n:n});
      } else if (jokers > 0) {
        run.push({s:-1, n:-1});
        jokers--;
      }
      else break;
      n++;
    }

    while (jokers-- > 0) {
      run.push({s:-1, n:-1});
    }
    return run;
  }

  Hand.prototype.findSet = function(s, n) {
    var set = [];
    while (s < 4) {
      for (var i = 0; i < this.cards[s][n]; i++) {
        set.push({s:s, n:n});
      }
      s++;
    }

    for (var i = 0; i < this.jokers; i++) {
      set.push({s:-1, n:-1});
    }
    return set;
  }

  Hand.prototype.removeCards = function(cards) {
    for (var i = 0; i < cards.length; i++) {
      if (cards[i].s >= 0 && cards[i].n < 13) {
        this.cards[cards[i].s][cards[i].n]--;
      } else if (cards[i].n == 13){
        this.cards[cards[i].s][0]--;
      } else this.jokers--;
    }
    this.value = this.leftoverValue();
  }

  Hand.prototype.leftoverValue = function() {
    var leftover = 0;
    for (var i = 0; i < 4; i++) {
      for (var j = 0; j < 13; j++) {
        value = j + 1;
        if(value > 10){
          value = 10;
        }
        leftover += this.cards[i][j] * value;
      }
    }
    return leftover + this.jokers * currentRound
  }

  function clone(a) {
    var b = [];
    for (var i = 0; i < a.length; i++) {
      b[i] = a[i].slice();
    }
    return b;
  }

  function showHand(c, j, v) {
    var num = "    A 2 3 4 5 6 7 8 9 T J Q K";
    console.log(num);
    for (var i = 0; i < 4; i++) {
      console.log(["SPD ","CLB ","HRT ","DMD "][i] + c[i]);
    }
    console.log("    jokers: " + j + "  value: " + v);
  }

  function showResult(m, v) {
    if (m.length == 0) console.log("no melds found");
    while (m.length) {
      var c = m.shift();
      if (c.s == -1) console.log("joker *");
      else console.log(["clubs","dmnds","heart","spade"][c.s] + " " + "3456789TJQK".charAt(c.n));
    }
    console.log("leftover value: " + v);
  }

  function calculateScore(ndeck) {
    var matrix = [];
    var jokers = 0;
    var round = currentRound;

    for (var i = 0; i < 4; i++) {
      matrix[i] = [];
      for (var j = 0; j < 13; j++) {
        matrix[i][j] = 0;
      }
    }
    
    for(var x = 0; x < ndeck.length; x++){
      card = ndeck[x]
      if(isWildcard(card)){
        jokers++;
      } else {
        matrix[card.getSuit()][card.getValue()]+=1;
      }
    }
    
    var x = new Hand(matrix, jokers);
    x.findMelds();
    return x.value;
  }

  function stringCard(card) {
    var result = "";
    result += card.getValue();
    result += " of ";
    result += card.getSuit();
    return result;
  }

  function stringDeck(deck) {
    var result = "";
    deck.forEach(function(item) {
      result += item.getValue() + " of " + item.getSuit() + "|";
    });
    return result;
  }

  function drawGameFinishedDialog(){
    var bitmap2 = new createjs.Bitmap(backImage);
    bitmap2.scale = cardScale * 2;
    bitmap2.x = leftbound + 300-250 * cardScale/2*2;
    bitmap2.y = topbound + 500-350 * cardScale/2*2;
    container.addChild(bitmap2);
    var toDisplay = []
    var player1txt = ""
    var player2txt = ""
    if(playerscore < opponentscore){
      toDisplay[2] = "You won!"
      if(user == player1){
        player1txt = "☆"
      } else {
        player2txt = "☆"
      }
    } else if(playerscore > opponentscore){
      toDisplay[2] = "Your opponent won!"
      if(user == player1){
        player2txt = "☆"
      } else {
        player1txt = "☆"
      }
    } else {
      toDisplay[2] = "It's a tie!"
      player1txt = "☆"
      player2txt = "☆"
    }
    if(user == player1){
      toDisplay[0] = player1txt + player1 + ": " + playerscore
    } else {
      toDisplay[0] = player1txt + player1 + ": " + opponentscore
    }
    if(user == player1){
      toDisplay[1] = player2txt + player2 + ": " + opponentscore
    } else {
      toDisplay[1] = player2txt + player2 + ": " + playerscore
    }
    var texts = []
    var extra = 0
    for(x = 0; x < toDisplay.length; x++){
      if(x == toDisplay.length - 1){
        extra = 300;
      }
      texts[x] = new createjs.Text(toDisplay[x], TEXTTYPE3, "#000000")
      texts[x].x = leftbound + 500 - 400;
      texts[x].y = topbound + 500 - 270 + 80 * x + extra;
      container.addChild(texts[x]);
    }
    dropConfetti();
    stage.update();
    if(user == player1){
      send('<SCORE>,' + player1 + ',' + playerscore + ',' + opponentscore + '/');
    } else {
      send('<SCORE>,' + player2 + ',' + opponentscore + ',' + playerscore + '/');
    }
  }

  function prepareForNextRound(){
    preparingForNextRound = true;
  }

  function nextRound(){
    createAndShuffleDeck();

    opponentHandCards = []
    opponentHandSuits = []

    playerHandCards = []
    playerHandSuits = []
    
    var cr = currentRound + 1
    var deckCount = cr*2+1
    canPlayerDiscard = false;
    console.log("Current round: " + cr);
    
    // FIXED: Properly initialize currentCard for new round
    var currentCard = cr*2 + 3;
    
    if(user == player1){
      console.log("Ready player 1")
      for (let i = 0; i < cr; i++) {
        playerHandCards[i] = deck[i].Value
        playerHandSuits[i] = deck[i].Suit
      }
      for (let i = cr; i < cr*2; i++) {
        opponentHandCards[i-cr] = deck[i].Value
        opponentHandSuits[i-cr] = deck[i].Suit
      }
      if(cr%2 == 0){
        canPlayerDraw = false;
      } else {
        canPlayerDraw = true;
      }
    } else {
      console.log("Ready player 2")
      for (let i = 0; i < cr; i++) {
        opponentHandCards[i] = deck[i].Value
        opponentHandSuits[i] = deck[i].Suit
      }
      for (let i = cr; i < cr*2; i++) {
        playerHandCards[i-cr] = deck[i].Value
        playerHandSuits[i-cr] = deck[i].Suit
      }
      if(cr%2 == 0){
        canPlayerDraw = true;
      } else {
        canPlayerDraw = false;
      }
    }
    
    firstdiscard = deck[cr*2 + 1].Value
    firstdiscardsuit = deck[cr*2 + 1].Suit

    discardcard = [firstdiscard]
    discardsuit = [firstdiscardsuit]
    setCurrentPlayer(canPlayerDraw);
    currentRound = currentRound + 1;
    preparingForNextRound = false;
    
    if(currentRound == 14){
      drawGameFinishedDialog();
    } else {
      gameOverOnNextDiscard = false;
      opponentWinsOnNextDiscard = false;
      
      // FIXED: Safely remove discard pile elements
      try {
        if(discard && container.contains(discard)){
          container.removeChild(discard);
        }
        if(lastDiscard && container.contains(lastDiscard)){
          container.removeChild(lastDiscard);
        }
      } catch(e) {
        console.log("Error removing discard: " + e);
      }
      
      sortHand(false);
      drawHand();
      drawDiscard()
      drawOpponentHand();
      if(currentRound%2 == 0){
        canPlayerDraw = (user != player1);
      } else {
        canPlayerDraw = (user == player1);
      }
      setCurrentPlayer(canPlayerDraw);
      setRoundText();
    }
  }

  function checkPlayerWin(){
    ndeck = []
    for(var x = 0; x < playerHandCards.length; x++){
      ndeck[ndeck.length] = (new Card(playerHandCards[x], playerHandSuits[x]))
    }
    score = calculateScore(ndeck)
    if(score == 0){
      gameOverOnNextDiscard = true;
      wonGame();
    }
  }

  function checkOpponentWin(){
    ndeck2 = []
    for(var x = 0; x < opponentHandCards.length; x++){
      ndeck2[ndeck2.length] = (new Card(opponentHandCards[x], opponentHandSuits[x]))
    }
    score = calculateScore(ndeck2);
    sortOpponentHand(true);
    if(score == 0) {
      opponentWinsOnNextDiscard = true;
      drawOpponentHandFaceup();
    }
  }

  var radius = 10;
  var buttonSize = 100;
  
  function drawSortButtons(){
    var button333 = new createjs.Shape();
    button333.graphics.beginFill("lightgreen").drawRoundRectComplex(leftbound + 1000 - buttonSize, topbound + 350 , buttonSize, buttonSize, radius,radius,radius,radius);
    var text333 = new createjs.Text("333", TEXTTYPE, "#000000")
    text333.x = leftbound + 1000 - 50;
    text333.textAlign = 'center';
    text333.y = topbound + 350 +30;

    container.addChild(button333)
    container.addChild(text333)
    button333.on("mousedown", function(event) {
      sortHand(false);
      sortHand(true);
      drawHand();
    });

    var button456 = new createjs.Shape();
    button456.graphics.beginFill("lightblue").drawRoundRectComplex(leftbound + 1000 - buttonSize, topbound + 550 , buttonSize, buttonSize, radius,radius,radius,radius);
    var text456 = new createjs.Text("456", TEXTTYPE, "#000000")
    text456.x = leftbound + 1000-50;
    text456.textAlign = 'center';
    text456.y = topbound + 550+30;

    container.addChild(button456)
    container.addChild(text456)
    button456.on("mousedown", function(event) {
      sortHand(false);
      drawHand();
    });
  }

  var discardx = 700;
  var discardy = 500;
  var discard;
  var lastDiscard;

  var discardcard = [firstdiscard]
  var discardsuit = [firstdiscardsuit]

  function takeDiscard(){
    if(discard && container.contains(discard)){
      container.removeChild(discard);
    }
    playerHandCards[playerHandCards.length] = discardcard[discardcard.length-1]
    playerHandSuits[playerHandSuits.length] = discardsuit[discardsuit.length-1]
    discardcard.splice(discardcard.length-1, 1);
    discardsuit.splice(discardsuit.length-1, 1);
    drawHand();
    if(discardcard.length > 0){
      drawDiscard();
    }
  }

  function opponentDrawDeck(){
    if(currentCard < 52){
      opponentHandCards[opponentHandCards.length] = deck[currentCard].Value
      opponentHandSuits[opponentHandSuits.length] = deck[currentCard].Suit
      currentCard++;
    } else {
      ndeck = []
      for(var x = 0; x < discardcard.length; x++){
        ndeck[ndeck.length] = (new Card(discardcard[x], discardsuit[x]))
      }
      currentCard = 1;
      discardcard = [ndeck[0].Value]
      discardsuit = [ndeck[0].Suit]
      deck = []
      for(var x = 1; x < ndeck.length; x++){
        deck[x-1] = ndeck[x]
      }
      drawDiscard();
    }
    drawOpponentHand();
    canPlayerDraw = false;
  }

  function opponentTakeDiscard(){
    if(discard && container.contains(discard)){
      container.removeChild(discard);
    }
    opponentHandCards[opponentHandCards.length] = discardcard[discardcard.length-1]
    opponentHandSuits[opponentHandSuits.length] = discardsuit[discardsuit.length-1]
    discardcard.splice(discardcard.length-1, 1);
    discardsuit.splice(discardsuit.length-1, 1);
    drawOpponentHand();
    if(discardcard.length > 0){
      drawDiscard();
    }
    canPlayerDraw = false;
  }

  function opponentDiscard(input){
    theDiscard = input.split('.')
    discardCard = parseInt(theDiscard[0])
    discardSuit = parseInt(theDiscard[1])
    
    nCards = []
    nSuits = []
    var count = 0;
    var first = true;
    
    for(var x = 0; x < opponentHandCards.length; x++){
      if(!(discardSuit == opponentHandSuits[x] && discardCard == opponentHandCards[x]) && first){
        nCards[count] = opponentHandCards[x];
        nSuits[count] = opponentHandSuits[x];
        count++;
      } else if (!first) {
        nCards[count] = opponentHandCards[x];
        nSuits[count] = opponentHandSuits[x];
        count++;
      } else {
        first = false;
      }
    }
    
    discardcard[discardcard.length] = discardCard
    discardsuit[discardsuit.length] = discardSuit
    opponentHandCards = nCards
    opponentHandSuits = nSuits
    drawOpponentHand();
    drawDiscard();
    checkPlayerWin();
    checkOpponentWin();
    canPlayerDraw = true;
    canPlayerDiscard = false;
    
    if(gameOverOnNextDiscard){
      wonGame();
    }
    
    setCurrentPlayer(true);
  }

  function drawDiscard(){
    if(lastDiscard && container.contains(lastDiscard)){
      container.removeChild(lastDiscard);
    }
    lastDiscard = discard
    discard = drawCard(discardsuit[discardsuit.length-1],discardcard[discardcard.length-1],discardx,discardy);
    discard.on("mousedown", function(event) {
      if(gameReady){
        console.log("canPlayerDraw: " + canPlayerDraw);
        if(canPlayerDraw && playerHandCards.length < currentRound + 1){
          takeDiscard();
          canPlayerDraw = false;
          canPlayerDiscard = true;
          send("draw,discard,"+user)
        }
      }
    });
  }
  
  var currentCard = currentRound*2 + 1 + 2;
  
  function drawCardFromDeck(){
    if(canPlayerDraw) {
      if(currentCard < 52){
        playerHandCards[playerHandCards.length] = deck[currentCard].Value
        playerHandSuits[playerHandSuits.length] = deck[currentCard].Suit
        currentCard++;
      } else {
        ndeck = []
        for(var x = 0; x < discardcard.length; x++){
          ndeck[ndeck.length] = (new Card(discardcard[x], discardsuit[x]))
        }
        currentCard = 1;
        discardcard = [ndeck[0].Value]
        discardsuit = [ndeck[0].Suit]
        deck = []
        for(var x = 1; x < ndeck.length; x++){
          deck[x-1] = ndeck[x]
        }
        drawDiscard();
      }
      canPlayerDraw = false;
      canPlayerDiscard = true;
      drawHand();
    }
  }

  function drawDeck(cardsInDeck) {
    var deckoffset = 5;
    for(var x = 0; x < cardsInDeck; x++){
      drawFacedownCard(300+deckoffset*(cardsInDeck-x),500+deckoffset*(cardsInDeck-x));
    }
    cardDeck = drawFacedownCard(300,500);
    cardDeck.on("mousedown", function(event) {
      if(gameReady){
        console.log('Can player draw is ' + canPlayerDraw);
        if(canPlayerDraw && playerHandCards.length < currentRound + 1){
          drawCardFromDeck();
          canPlayerDraw = false;
          canPlayerDiscard = true;
          send("draw,deck,"+user)
        }
      }
    });
  }

  function beginGame(){
    sortHand(false);
    drawHand();
    drawDeck(4);
    drawOpponentHand();
    drawDiscard();
    drawSortButtons();
    stage.update();
  }

  let gameplay;

  function send(text){
    gameSocket.send(text + '/');
    canPlayerDraw = false;
    currentTurn++;
  }

  var opjContainer;
  var joinShowed = false;
  
  function opponentJoinedGame(){
    if(!joinShowed){
      opjContainer = new createjs.Container();
      var opjText = new createjs.Text("Opponent Joined Game", TEXTTYPE, "#000000")
      opjText.x = leftbound + 500;
      opjText.y = topbound + 270;
      opjText.textAlign = 'center';
      opjContainer.addChild(opjText);
      setTimeout(() => {
        if(container.contains(opjContainer)){
          container.removeChild(opjContainer);
        }
      }, 5000);
      container.addChild(opjContainer);
    }
    if(user == player1){
      canPlayerDraw = true;
    }
    joinShowed = true;
  }
  
  var playerscore = 0;
  var psoffset = 30;
  var playerScore = new createjs.Shape();
  playerScore.graphics.beginFill("lightyellow").drawRoundRectComplex(leftbound, topbound + 550 , buttonSize, buttonSize, radius,radius,radius,radius);
  var playerScoreText = new createjs.Text("--", TEXTTYPE, "#000000")
  playerScoreText.x = leftbound + 50;
  playerScoreText.textAlign = 'center';
  playerScoreText.y = topbound + 550 + 30;

  var currentPlayer = new createjs.Text("☆", TEXTTYPE2, "#E8CD71")
  currentPlayer.x = leftbound + 50;
  currentPlayer.textAlign = 'center';
  if(user == player1){
    currentPlayer.y = topbound + 700-psoffset;
  } else {
    currentPlayer.y = topbound + 300-psoffset;
  }

  container.addChild(currentPlayer)

  function setCurrentPlayer(userOrOpponent){
    if(userOrOpponent) {
      currentPlayer.y = topbound + 700-psoffset;
    } else {
      currentPlayer.y = topbound + 300-psoffset;
    }
  }

  var circle = new createjs.Shape();
  circle.graphics.beginFill("#E8CD71").drawCircle(0, 0, 50);
  circle.x = leftbound + 500;
  circle.y = topbound + 500;
  container.addChild(circle);

  var roundtext = new createjs.Text("", TEXTTYPE2, "#000000")
  roundtext.x = leftbound + 500;
  roundtext.y = topbound + 500 - 30;
  roundtext.textAlign = 'center';

  container.addChild(roundtext)

  function setRoundText(){
    roundtext.text = cardnames[currentRound-1];
    stage.update();
  }
  setRoundText();

  var opponentscore = 0;

  var opponentScore = new createjs.Shape();
  opponentScore.graphics.beginFill("#f0655b").drawRoundRectComplex(leftbound, topbound + 350 , buttonSize, buttonSize, radius,radius,radius,radius);
  var opponentScoreText = new createjs.Text("--", TEXTTYPE, "#000000")
  opponentScoreText.x = leftbound + 50;
  opponentScoreText.textAlign = 'center';
  opponentScoreText.y = topbound + 350 + 30;
  container.addChild(playerScore)
  container.addChild(opponentScore)
  container.addChild(opponentScoreText)
  container.addChild(playerScoreText)

  function drawPlayerScore(input){
    playerScoreText.text = input
  }

  function drawOpponentScore(input){
    opponentScoreText.text = input
  }

  var recovered = false;
  
  function recoverState(gp){
    recoveringState = true;
    for(let i = 0; i < gp.length-1; i++){
      console.log("Recovering turn: " + gp[i]);
      sp = gp[i].split(",");
      
      if(sp[0] == "join" && sp[2] != user){
        console.log("Opponent Joined");
      } else if(sp[0] == "draw" && sp[2] != user){
        if(sp[1] == "deck"){
          opponentDrawDeck();
        } else if(sp[1] == "discard"){
          opponentTakeDiscard();
        }
      } else if(sp[0] == "discard" && sp[2] != user){
        opponentDiscard(sp[1]);
        canPlayerDraw = true;
      } else if(sp[0] == "draw" && sp[2] == user){
        canPlayerDraw = true;
        if(sp[1] == "deck"){
          drawCardFromDeck();
        } else if(sp[1] == "discard"){
          takeDiscard();
        }
        canPlayerDraw = false;
        canPlayerDiscard = true;
      } else if(sp[0] == "discard" && sp[2] == user){
        canPlayerDiscard = true;
        theDiscard = sp[1].split('.')
        discardCard = parseInt(theDiscard[0])
        discardSuit = parseInt(theDiscard[1])
        playerDiscard(discardCard, discardSuit);
        canPlayerDiscard = false;
        if(gameIsWon){
          if(container.contains(wonContainer)){
            container.removeChild(wonContainer);
          }
          nextRound();
          gameIsWon = false;
        }
      }
    }
    currentTurn = gp.length-1;
    recoveringState = false;
  }

  function readCallback(){
    gp = gameplay;
    if(!gameReady){
      gameReady = true;
    }
    if(!recovered && gp.length > 2){
      console.log("Recovering state");
      recovered = true;
      recoverState(gp);
    } else if(!recovered){
      recovered = true;
    }
    
    var ind = currentTurn;
    var end = gp.length - 1;
    if(gp.length <= 2) currentTurn = 0;
    
    for(let i = currentTurn; i < end; i++){
      sp = gp[i].split(",");
      
      if(sp[0] == "join" && sp[2] != user){
        opponentJoinedGame();
        currentTurn = i+1;
      } else if(sp[0] == "draw" && sp[2] != user){
        if(sp[1] == "deck"){
          opponentDrawDeck();
        } else if(sp[1] == "discard"){
          opponentTakeDiscard();
        }
        canPlayerDraw = false;
        currentTurn = i+1;
      } else if(sp[0] == "discard" && sp[2] != user){
        if(gameIsWon) {
          nextRound();
          gameIsWon = false;
          if(container.contains(wonContainer)){
            container.removeChild(wonContainer);
          }
        }
        opponentDiscard(sp[1]);
        canPlayerDraw = true;
        currentTurn = i+1;
      }
    }
    stage.update();
  }

  function read(text){
    gameplay = text.split("/");
    readCallback();
  }

  function gameplayArray(){
    return gameplay.split('/');
  }

  function createArray(length) {
    let arr = new Array(length || 0),
      i = length;

    if (arguments.length > 1) {
      let args = Array.prototype.slice.call(arguments, 1);
      while (i--) arr[length - 1 - i] = createArray.apply(this, args);
    }
    return arr;
  }

  var colors = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple"];
  var COLORS = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple"];
  let confettiCount = 60;
  let confetti = [];
  let confettivx = [];
  let confettivy = [];
  let confettiv = 10;
  let confettimin = -600;
  var droppedConfetti = false;

  function drawConfetti() {
    for (i = 0; i < confettiCount; i++) {
      confetti[i] = new createjs.Shape();
      confetti[i].graphics.beginFill(COLORS[0, rng.nextRange(0, COLORS.length)]).drawCircle(0, 0, rng.nextRange(7, 15));
      confetti[i].x = rng.nextRange(0, stage.canvas.width);
      confetti[i].y = rng.nextRange(stage.canvas.height + 30);
      confetti[i].visible = false;
      confettivx[i] = rng.nextRange(-1, 1) / 5.0;
      confettivy[i] = rng.nextRange(-1, 1) / 5.0;
      stage.addChild(confetti[i]);
    }
  }

  function dropConfetti() {
    drawConfetti();
    droppedConfetti = false;
    for (i = 0; i < confettiCount; i++) {
      confetti[i].visible = true;
      confetti[i].y = rng.nextRange(confettimin, -20);
      confetti[i].x = rng.nextRange(0, stage.canvas.width);
      confettivx[i] = rng.nextRange(-3, 3) / 7.0;
      confettivy[i] = rng.nextRange(-3, 3) / 3.0;
    }
  }

  drawConfetti();

  createjs.Ticker.setFPS(60);
  createjs.Ticker.addEventListener("tick", stage);
  createjs.Ticker.addEventListener("tick", handleTick2);
  
  function handleTick2(event) {
    if (!droppedConfetti) {
      dropped = true;
      for (i = 0; i < confettiCount; i++) {
        if (confetti[i].y < window.innerHeight + 20) {
          confetti[i].x = confetti[i].x + confettivx[i]
          confetti[i].y = confetti[i].y + confettivy[i] + confettiv
          dropped = false;
        } else {
          confetti[i].visible = false;
        }
      }
      if (dropped) {
        droppedConfetti = true;
      }
    }
    stage.update();
  }

  function calculateAndDrawScores(){
    lastOpponentScore = calculateOpponentScore();
    lastPlayerScore = calculatePlayerScore();
    opponentscore+=lastOpponentScore;
    playerscore+=lastPlayerScore;
    drawOpponentScore(opponentscore);
    drawPlayerScore(playerscore);
  }

  let wonContainer;
  let wonDialog;
  
  function wonGame() {
    if(!gameIsWon){
      calculateAndDrawScores();
      gameIsWon = true;
      wonContainer = new createjs.Container();
      wonDialog = new createjs.Shape();
      wonDialog.graphics.beginFill("lightgreen").drawCircle(0, 0, 1000);
      wonDialog.y = topbound + 1000 + 900;
      wonDialog.x = leftbound + 500;
      var txt = "";
      if(lastPlayerScore == 0 && lastOpponentScore == 0){
        txt = "You both won!"
      } else if(lastPlayerScore == 0) {
        txt = "You won!"
      } else if(lastOpponentScore == 0) {
        txt = "Your opponent won!"
      }
      txt = txt + " (Tap)"
      let wonText = new createjs.Text(txt, TEXTTYPE, "#000000")
      wonText.x = leftbound + 500;
      wonText.y = topbound + 935;
      wonText.textAlign = 'center'
      drawOpponentHandFaceup();
      prepareForNextRound();
      wonContainer.addChild(wonDialog);
      wonContainer.addChild(wonText);
      container.addChild(wonContainer);
      if(!recoveringState) {
        wonContainer.on("mousedown", function(event) {
          if(container.contains(wonContainer)){
            container.removeChild(wonContainer);
          }
          nextRound();
          gameIsWon = false;
        });
      } else {
        if(container.contains(wonContainer)){
          container.removeChild(wonContainer);
        }
        nextRound();
        gameIsWon = false;
      }
    }
  }

  function calculateOpponentScore(){
    ndeck2 = []
    for(var x = 0; x < opponentHandCards.length; x++){
      ndeck2[ndeck2.length] = (new Card(opponentHandCards[x], opponentHandSuits[x]))
    }
    score = calculateScore(ndeck2)
    return score
  }

  function calculatePlayerScore(){
    ndeck = []
    for(var x = 0; x < playerHandCards.length; x++){
      ndeck[ndeck.length] = (new Card(playerHandCards[x], playerHandSuits[x]))
    }
    score = calculateScore(ndeck)
    return score
  }

  function opponentWonGame() {
    if(!gameIsWon){
      calculateAndDrawScores();
      if(user == player1){
        if((currentRound+1)%2 == 1){
          canPlayerDraw = true;
        } else {
          canPlayerDraw = false;
        }
      } else {
        if((currentRound+1)%2 == 0){
          canPlayerDraw = true;
        } else {
          canPlayerDraw = false;
        }
      }
      gameIsWon = true;
      wonContainer = new createjs.Container();
      wonDialog = new createjs.Shape();
      wonDialog.graphics.beginFill("lightblue").drawCircle(0, 0, 1000);
      wonDialog.y = topbound + 1000 + 900;
      wonDialog.x = leftbound + 500;
      var txt = ""
      if(lastPlayerScore == 0 && lastOpponentScore == 0){
        txt = "You both won!"
      } else if(lastPlayerScore == 0) {
        txt = "You won!"
      } else if(lastOpponentScore == 0) {
        txt = "Your opponent won!"
      }
      txt = txt + " (Tap)"
      let wonText = new createjs.Text(txt, TEXTTYPE, "#000000")
      wonText.textAlign = 'center'
      wonText.x = leftbound + 500;
      wonText.y = topbound + 935;
      wonContainer.on("mousedown", function(event) {
        if(container.contains(wonContainer)){
          container.removeChild(wonContainer);
        }
        gameIsWon = false
        nextRound();
      });
      drawOpponentHandFaceup();
      prepareForNextRound();
      wonContainer.addChild(wonDialog);
      wonContainer.addChild(wonText);
      container.addChild(wonContainer);
    }
  }
  
  let ticks = 0;
  stage.update();
})();
