import React, {
  Component
} from 'react';
import update from 'immutability-helper';
import './App.css';
import autobahn from 'autobahn';


function suitToSymbol(suit) {
  switch (suit) {
    case "C":
      return "\u2663";
    case "D":
      return "\u2666";
    case "H":
      return "\u2665";
    case "S":
      return "\u2660";
    default:
      return undefined;
  }
}

function UIButton(props) {
  return (
    <div className="button" onClick={() => props.onClick()}>{props.children}</div>
  )
}

class Card extends Component {
  render() {
    return (
      <div
        className={`card${this.props.color}`}
        onClick={() => this.props.onClick()}
      >
        {this.props.children}
      </div>
    );
  }
}

class FaceDownHand extends Component {
  render() {
    const n = this.props.size;
    return (
      <div className="hand tophand">
        {[...Array(n)].map((x, i) =>
          <Card
            key={i}
            color="black"
            onClick={() => false} />
         )
        }
      </div>
    );
  }
}


function AloneControl(props) {
  return (
    <div className={props.className}>
      <span className="control-label">Go alone?</span>
      <UIButton onClick={() => props.onClick(true)}>Yes</UIButton>
      <UIButton onClick={() => props.onClick(false)}>No</UIButton>
    </div>
  );
}

class Bid1Controls extends Component {
  constructor() {
    super();
    this.state = {stage: "CALL"};
  }

  render() {
    switch (this.state.stage) {
      case "CALL":
        return (
          <div className={this.props.className}>
            <UIButton onClick={() => this.setState({stage: "ALONE"})}>Pick it up</UIButton>
            <UIButton onClick={() => this.props.pass()}>Pass</UIButton>
          </div>
        );
      case "ALONE":
        return <AloneControl className={this.props.className} onClick={(alone) => this.props.call(alone)}/>;
      default:
        return null;
    }
  }
}

class Bid2Controls extends Component {
  constructor() {
    super();
    this.state = {stage: "CALL"};
  }

  render() {
    switch (this.state.stage) {
      case "CALL":
        return (
          <div className={this.props.className} >
            <UIButton onClick={() => this.setState({stage: "TRUMP"})}>Name trump</UIButton>
            <UIButton onClick={() => this.props.pass()}>Pass</UIButton>
          </div>
        );
      case "TRUMP":
        return (
          <div className={this.props.className}>
            <span className="control-label">Trump:</span>
            {
              "CDHS".split('').map((c) =>
                <UIButton onClick={() => this.setState({stage: "ALONE", trump: c})}>{suitToSymbol(c)}</UIButton>
              )
            }
          </div>
        );
      case "ALONE":
        return <AloneControl className={this.props.className} onClick={(alone) => this.props.call(this.state.trump, alone)}/>;
      default:
        return null;
    }
  }
}

class FaceUpCard extends Component {
  constructor(props) {
    super(props);
    if (this.props.suit === "D" || this.props.suit === "H") {
      this.color = "red";
    } else {
      this.color = "black";
    }

    this.suitSymbol = suitToSymbol(this.props.suit);
  }

  render() {
    return (
      <Card color={this.color} onClick={() => this.props.onClick()}>
        {this.props.rank + this.suitSymbol}
      </Card>
    );
  }

  static fromStr(s, onClick) {
    const [rank, suit] = s.split('.');
    return (
      <FaceUpCard suit={suit} rank={rank} key={rank + suit} onClick={onClick} />
    );
  }
}

class Hand extends Component {
  render() {
    const cardStrs = this.props.cards
    return (
      <div className="hand myhand">{cardStrs.map((cardStr, index) => {
          return (
            FaceUpCard.fromStr(cardStr, () => this.props.onClick(index))
          );
        })}
      </div>
    );
  }
}

class Trick extends Component {
  render() {
    const bottom = this.props.player;
    const left = (this.props.player + 1) % 4;
    const top = (this.props.player + 2) % 4;
    const right = (this.props.player + 3) % 4;
    const cards = this.props.cards;
    return (
      <div >
      {cards[top] &&
       <div className="tricktop trickcard">
         {FaceUpCard.fromStr(cards[top], () => false) }
       </div>
      }
      {cards[bottom] &&
       <div className="trickbot trickcard">
         {FaceUpCard.fromStr(cards[bottom], () => false) }
       </div>
      }
      {cards[left] &&
       <div className="trickleft trickcard">
         {FaceUpCard.fromStr(cards[left], () => false) }
       </div>
      }
      {cards[right] &&
       <div className="trickright trickcard">
         {FaceUpCard.fromStr(cards[right], () => false) }
       </div>
      }
      </div>
    );
  }
}

function Scoreboard(props) {
  const yourTeam = props.team;
  const otherTeam = 1 - yourTeam;
  return (
    <div style={{textAlign: "left"}}>
      {(props.dealing) ? <div>You are the dealer</div> : null}
      {(props.turn) ? <div>It's your turn</div> : null}
      {(props.trump !== undefined) ? <div>Trump: {props.trump}</div> : null}
      <div>Tricks taken: {props.tricks[yourTeam]}–{props.tricks[otherTeam]} </div>
      <div>Score: {props.scores[yourTeam]}–{props.scores[otherTeam]}</div>
    </div>
  );
}

class App extends Component {
  constructor() {
    super();
    this.state = {
      hand: [],
      upcard: null,
      phase: null,
      turn: null,
      dealer: null,
      alone: null,
      trickScore: [0, 0],
      score: [0, 0],
      tricks: []
    };

    /* const wsuri = "ws://localhost:8080/ws";*/
    const wsuri = `ws://${document.location.hostname}:8080/ws`

    // the WAMP connection to the Router
    this.connection = new autobahn.Connection({
      url: wsuri,
      realm: "realm1"
    });

    // fired when connection is established and session attached
    this.connection.onopen = (session, details) => {
      this.session = session;
      console.log("Connected");

      session.call('realm1.create_player', ["Fred"])
        .then((res) => {
          console.log(`Player ID: ${res}`);
          this.player = res;
          session.call("realm1.join_table", [res, res])
            .then(console.log);
          session.subscribe(`realm1.p${this.player}.hand`,
            (res) => {this.setState({"hand": res[0]}); console.log(res[0]);});
          session.subscribe('realm1.state',
            (res) => this.setState(res[0]));
          session.subscribe('realm1.card_played',
                            ((res) => this.pushCard(res[0][0], res[0][1])));
          session.subscribe('realm1.msg',
                            (res) => console.log(res[0]));
          session.subscribe('realm1.newhand', (res) => this.newHand());
          session.subscribe('realm1.newtrick', (res) => this.newTrick());
          console.log("subscribed");
        })
        .catch(console.log);
    };

    // fired when connection was lost (or could not be established)
    //
    this.connection.onclose = function(reason, details) {
      console.log("Connection lost: " + reason);
    }

    // now actually open the connection
    this.connection.open();
  }

  newTrick() {
    this.setState((prevState) =>
      update(prevState, {
        tricks: {
          $push: [[...Array(4)]]
        }
      }));
  }

  newHand() {
    this.setState({tricks: []});
  }

  pushCard(card, position) {
    const currentIndex = this.state.tricks.length - 1;
    this.setState((prevState) =>
      update(prevState, {
        tricks: {
          [currentIndex]: {
            [position]: {$set: card}
          }
        }
      })
    );
  }

  run() {
    this.session.call('realm1.run');
  }

  removeCard(index) {
    this.setState((prevState) =>
      update(prevState, {
        hand: {
          $splice: [
            [index, 1]
          ]
        }
      })
    );
  }

  handleCardClick(i) {
    if (!this.myTurn()) {
      return;
    }
    const phase = this.state.phase;
    const hand = this.state.hand;
    if (phase !== "play" && phase !== "discard") {
      return;
    }

    this.session.call(`realm1.p${this.player}.${phase}`,
                        [this.state.hand[i]])
        .then((res) => {
          // QUESTIONABLE HACK
          if (res && hand === this.state.hand) {
            this.removeCard(i);
          } else {
            console.log("turn error");
          }
        });
  }

  bid1(call, alone) {
    this.session.call(`realm1.p${this.player}.bid1`,
                      [call, alone]);
  }

  bid2(call, alone, suit) {
    this.session.call(`realm1.p${this.player}.bid2`,
                      [call, alone, suit]);
  }

  myTurn() {
    return this.state.turn === this.player;
  }

  renderBidControls() {
    if (this.myTurn()) {
      switch (this.state.phase) {
        case "bid1":
          return (
            <Bid1Controls
              className="bid-controls"
              call={(alone) => this.bid1(true, alone)}
              pass={() => this.bid1(false, false)}
            />
          );
        case "bid2":
          return (
            <Bid2Controls
              className="bid-controls"
              call={(trump, alone) => this.bid2(true, trump, alone)}
              pass={() => this.bid2(false, false, null)}
            />
          );
        default:
          return null;
      }
    }
  }

  debugHand() {
    this.player = 1;
    this.setState({
      hand: ["K.H",
             "Q.D",
             "10.H",
             "J.S",
             "A.C"
      ],
      upcard: "J.D",
      turn: 1,
      phase: "bid2"
    });
  }

  handSize(player) {
    if (this.state.alone === player) {
      return 0;
    }
    const tricks = this.state.tricks;
    const playedCards = tricks.map((trick) => trick[player]).filter((x) => !!x);
    return 5 - playedCards.length;
  }

  render() {
    const topPlayer = (this.player + 2) % 4;
    const team = this.player % 2;
    const phase = this.state.phase;
    let currentTrick;
    if (phase === "play") {
      currentTrick = this.state.tricks[this.state.tricks.length - 1];
    }
    return (
      <div className="App">
        <FaceDownHand size={this.handSize(topPlayer)} />
        {this.state.phase && this.state.phase.startsWith("bid") &&
         <div className="upcard">
           {FaceUpCard.fromStr(this.state.upcard, () => false)}
         </div>}
        <div>Player {this.player}</div>
        <Hand cards={this.state.hand} onClick={(i) => this.handleCardClick(i)} />
        {this.renderBidControls()}
        {phase === "play" && <Trick player={this.player} cards={currentTrick} />} 
        <Scoreboard
          dealing={this.state.dealer === this.player}
          scores={this.state.score}
          team={team}
          tricks={this.state.trickScore}
          trump={this.state.trump}
          turn={this.myTurn()}
        />
        <div className="debug-buttons" >
          <UIButton onClick={() => this.run()} >run</UIButton>
          <UIButton onClick={() => this.debugHand()}>debug</UIButton>
        </div>
      </div>
    );
  }
}

export default App;
