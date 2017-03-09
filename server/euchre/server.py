import json
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from bidict import bidict
from .game import Game, initial_game_state
from .encoder import CardEncoder, PublicStateEncoder


class Lobby:
    def __init__(self, lobby_id, coordinator):
        self.lobby_id = lobby_id
        self.coordinator = coordinator
        self.game = None
        self.members = set()
        self.seats_to_players = bidict()

    def change_seat(self, player, seat):
        self.join_seat(player, seat)
        self.leave_seat(player)

    def check_seat_open(self, seat):
        if seat < 0 or seat > 3:
            raise RuntimeError("No such seat.")
        if seat in self.seats_to_players:
            raise RuntimeError("Seat is taken.")

    def join_lobby(self, player):
        self.members.add(player)

    def join_seat(self, player, seat):
        if player not in self.members:
            raise RuntimeError("Not in this lobby.")
        self.check_seat_open(seat)
        self.seats_to_players[seat] = player

    def leave_seat(self, player):
        del(self.seats_to_players.inv[player])

    def perform_move(self, move, player, *args, **kwargs):
        self.game.perform_move(move, self.seats_to_players.inv[player],
                               *args, **kwargs)
        self.coordinator.publish_state(self)

    def start_game(self):
        self.game = Game(initial_game_state())


class Player:
    def __hash__(self):
        return self.player_id

    def __init__(self, player_id, name, coordinator):
        self.player_id = player_id
        self.name = name
        self.coordinator = coordinator

    def change_seat(self, lobby_id, seat):
        self.coordinator.lobbies[lobby_id].change_seat(self, seat)

    def create_lobby(self):
        lobby = self.coordinator.create_lobby()
        lobby.join_lobby(self)
        return lobby.lobby_id

    def join_lobby(self, lobby_id):
        self.coordinator.lobbies[lobby_id].join_lobby(self)

    def join_seat(self, lobby_id, seat):
        self.coordinator.lobbies[lobby_id].join_seat(self, seat)

    def perform_move(self, lobby_id, move, *args, **kwargs):
        self.coordinator.lobbies[lobby_id].perform_move(move, self, *args,
                                                        **kwargs)

    def start_game(self, lobby_id):
        self.coordinator.lobbies[lobby_id].start_game()


class Coordinator(ApplicationSession):
    def create_lobby(self):
        lobby_id = self.lobby_count
        self.lobby_count += 1
        lobby = Lobby(lobby_id, self)
        self.lobbies[lobby_id] = lobby
        return lobby

    def publish_state(self, lobby):
        lobby_prefix = 'lobby{n}'.format(n=lobby.lobby_id)
        self.publish(
            '{lp}.publicstate'.format(lp=lobby_prefix),
            json.loads(json.dumps(lobby.game.state, cls=PublicStateEncoder)))
        for seat, player in lobby.seats_to_players.items():
            self.publish(
                '{lp}.hands.player{pn}'.format(lp=lobby_prefix,
                                               pn=player.player_id),
                json.loads(json.dumps(lobby.game.state.hands[seat],
                                      cls=CardEncoder)))

    async def onJoin(self, details):
        print("session joined")
        print("Details: {}".format(details))

        self.players = dict()
        self.player_count = 0
        self.lobbies = dict()
        self.lobby_count = 0

        async def join_server():
            player_id = self.player_count
            self.player_count += 1
            name = "Player {}".format(player_id)
            player = Player(player_id, name, self)
            self.players[player_id] = player

            await self.register(
                player.perform_move,
                'player{n}.perform_move'.format(n=player_id))
            await self.register(
                player.create_lobby,
                'player{n}.create_lobby'.format(n=player_id))
            await self.register(
                player.join_lobby,
                'player{n}.join_lobby'.format(n=player_id))
            await self.register(
                player.start_game,
                'player{n}.start_game'.format(n=player_id))
            await self.register(
                player.join_seat,
                'player{n}.join_seat'.format(n=player_id))

            return player_id, name

        await self.register(join_server, 'join_server')


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://localhost:8080/ws", realm=u"realm1")
    runner.run(Coordinator)