import unittest
from unittest.mock import *
from euchre.objects import *
from euchre.exceptions import *


# class CardTest(unittest.TestCase):
#     def test_valid_cards(self):
#         self.assertRaises(ValueError, Card, "10", "F")
#         self.assertRaises(ValueError, Card, "8", "F")
#         try:
#             Card("10", "C")
#         except ValueError:
#             self.fail("Card(\"10\", \"C\") raised ValueError")

#     def test_eq(self):
#         self.assertTrue(Card("J", "H"), Card("j", "h"))
class GameplayTest(unittest.TestCase):
    def configure(self):
        self.table = Table()
        self.players = [Player() for _ in range(4)]
        for i, p in enumerate(self.players):
            p.setName(str(i))
            p.joinTable(self.table, i)

    @staticmethod
    def cardKey(x):
        suitKey = {Suit.clubs: 1,
                   Suit.diamonds: 2,
                   Suit.hearts: 3,
                   Suit.spades: 4
                   }
        return (suitKey[x.suit], int(x.rank))

    @staticmethod
    def cardSort(deck):
        deck.remaining.sort(key=GameplayTest.cardKey)


class DeckTest(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()

    def test_deck(self):
        self.assertIn(Card(Rank.ten, Suit.clubs), self.deck.cards)

    def test_colors(self):
        self.assertEqual(Color.red, Suit.diamonds.color)
        self.assertEqual(Color.red, Suit.hearts.color)
        self.assertEqual(Color.black, Suit.spades.color)
        self.assertEqual(Color.black, Suit.clubs.color)

    def test_draw(self):
        myCard = self.deck.draw()
        self.assertIn(myCard, self.deck.cards)
        self.assertNotIn(myCard, self.deck.remaining)


class TrickTest(GameplayTest):
    @patch('euchre.objects.Deck.shuffle',
           new=GameplayTest.cardSort)
    def setUp(self):
        self.configure()
        self.table.begin()
        self.p1 = self.table.players[0]
        self.p2 = self.table.players[1]
        self.hand = Hand(self.table, self.p1)
        self.table.hand = self.hand
        self.hand.phase = PlayPhase(self.hand, Suit.spades,
                                    self.p2, False)
        self.trick = Trick(self.hand.phase, self.p2)
        self.hand.phase.trick = self.trick
        self.trick.run()

    def test_relativeSuit(self):
        self.assertTrue(self.trick.following(Card.fromStrs("10", "H")))
        self.p2.playCard(Card(Rank.nine, Suit.spades))
        self.assertEqual(Suit.spades,
                         self.trick.relativeSuit(Card.fromStrs("J", "C")))
        self.assertEqual(Suit.spades,
                         self.trick.relativeSuit(Card.fromStrs("Q", "S")))
        self.assertEqual(Suit.clubs,
                         self.trick.relativeSuit(Card.fromStrs("Q", "C")))
        self.assertEqual(Suit.spades,
                         self.trick.relativeSuit(Card.fromStrs("10", "S")))
        self.assertTrue(self.trick.following(Card.fromStrs("J", "C")))
        self.assertFalse(self.trick.following(Card.fromStrs("J", "H")))

    @patch('euchre.objects.Trick.ledSuit')
    def test_relativeRank(self, ledSuitMock):
        ledSuitMock.return_value = Suit.spades
        self.assertEqual((2, 21),
                         self.trick.relativeRank(Card.fromStrs("J", "S")))
        self.assertEqual((2, 20),
                         self.trick.relativeRank(Card.fromStrs("J", "C")))
        self.assertEqual((0, 12),
                         self.trick.relativeRank(Card.fromStrs("Q", "C")))

    @patch('euchre.objects.PlayPhase.trickWon')
    def test_play(self, wonMock):
        self.trick.play(self.p2, Card(Rank.jack, Suit.diamonds))
        self.assertEqual(self.trick.Play(Card(Rank.jack,
                                              Suit.diamonds), self.p2),
                         self.trick.cards[0])
        self.assertEqual(self.players[2], self.hand.phase.turn())
        self.assertFalse(wonMock.called)
        self.trick.play(self.players[2], Card(Rank.jack, Suit.diamonds))
        self.trick.play(self.players[3], Card(Rank.jack, Suit.diamonds))
        self.trick.play(self.players[0], Card(Rank.jack, Suit.diamonds))
        self.assertTrue(wonMock.called)

# class TableTest(unittest.TestCase):
#     def setUp(self):
#         self.t = Table()

#     def test_itPlayers(self):
#         cycle = [2, 3, 0, 1]
#         it = self.t.itPlayers(2)
#         for i in cycle:
#             self.assertEqual(i, next(it).n)

#     def test_itPlayers2(self):
#         cycle = [2, 3, 0]
#         it = self.t.itPlayers(2, excluded={self.t.players[1]})
#         for i in cycle:
#             self.assertEqual(i, next(it).n)

#     @patch('euchre.objects.Table.win')
#     def test_updateScore(self, winMock):
#         self.t = Table()
#         for i in range(10):
#             self.t.updateScore(i % 2, 1)
#         self.assertEqual(5, self.t.points[0])
#         self.assertEqual(5, self.t.points[1])
#         self.assertFalse(self.t.won)
#         self.assertFalse(winMock.called)

#         for i in range(9):
#             self.t.updateScore(i % 2, 1)
#         self.assertEqual(10, self.t.points[0])
#         self.assertEqual(9, self.t.points[1])
#         self.assertTrue(self.t.won)
#         self.assertTrue(winMock.called)


# class HandTest(unittest.TestCase):
#     @patch('euchre.objects.Deck.shuffle',
#            new=lambda self: self.remaining.sort())
#     def setUp(self):
#         self.t = Table()
#         self.h = Hand(self.t, self.t.players[0])

#     def test_deal(self):
#         self.assertEqual(self.h.upCard, Card("J", "C"))
#         for card in self.t.players[0].hand:
#             self.assertEqual("S", card.suit)

#     @patch('euchre.objects.Player.pickUp')
#     @patch('euchre.objects.Player.bid1')
#     def test_bid1_call_partner(self, bidMock, pickUpMock):
#         bidMock.side_effect = \
#                 [{'call': False},
#                  {'call': False},
#                  {'call': True, 'alone': False}]
#         result = self.h.bid1()
#         self.assertTrue(result)
#         self.assertEqual("C", self.h.trump)
#         self.assertEqual(self.t.players[1], self.h.leader)
#         self.assertIsNone(self.h.out)
#         self.assertTrue(pickUpMock.called)

#     @patch('euchre.objects.Player.pickUp')
#     @patch('euchre.objects.Player.bid1')
#     def test_bid1_call_alone(self, bidMock, pickUpMock):
#         bidMock.side_effect = \
#                 [{'call': False},
#                  {'call': True, 'alone': True}]
#         result = self.h.bid1()
#         self.assertTrue(result)
#         self.assertEqual("C", self.h.trump)
#         self.assertEqual(self.t.players[0], self.h.out)
#         self.assertEqual(self.t.players[3], self.h.leader)
#         self.assertFalse(pickUpMock.called)

#     @patch('euchre.objects.Player.pickUp')
#     @patch('euchre.objects.Player.bid2')
#     def test_bid2_call_alone(self, bidMock, pickUpMock):
#         bidMock.side_effect = \
#                 [{'call': False},
#                  {'call': False},
#                  {'call': True, 'suit': 'C', 'alone': True}]
#         result = self.h.bid2()
#         self.assertTrue(result)
#         self.assertEqual("C", self.h.trump)
#         self.assertEqual(self.t.players[1], self.h.out)
#         self.assertEqual(self.t.players[0], self.h.leader)
#         self.assertFalse(pickUpMock.called)

#     @patch('euchre.objects.Hand.scoreRound')
#     @patch('euchre.objects.Player.pickUp')
#     @patch('euchre.objects.Hand.playRound')
#     @patch('euchre.objects.Player.bid1')
#     @patch('euchre.objects.Hand.bid2')
#     def test_run_1(self, hMock, pMock, rMock, pickMock, scoreMock):
#         pMock.return_value = {'call': True, 'alone': False}
#         self.h.run()
#         self.assertFalse(hMock.called)
#         self.assertTrue(rMock.called)
#         self.assertTrue(pickMock.called)

#     @patch('euchre.objects.Hand.scoreRound')
#     @patch('euchre.objects.Player.pickUp')
#     @patch('euchre.objects.Hand.playRound')
#     @patch('euchre.objects.Player.bid1')
#     @patch('euchre.objects.Hand.bid2')
#     def test_run_2(self, hMock, pMock, rMock, pickMock, scoreMock):
#         pMock.return_value = {'call': False}
#         self.h.run()
#         self.assertTrue(hMock.called)
#         self.assertTrue(rMock.called)
#         self.assertFalse(pickMock.called)

#     @patch('euchre.objects.Hand.scoreRound')
#     @patch('euchre.objects.Player.pickUp')
#     @patch('euchre.objects.Hand.playRound')
#     @patch('euchre.objects.Player.bid2')
#     @patch('euchre.objects.Player.bid1')
#     def test_run_3(self, pMock, pMock2, rMock, pickMock, scoreMock):
#         pMock.return_value = {'call': False}
#         pMock2.return_value = {'call': False}
#         self.h.run()
#         self.assertFalse(rMock.called)
#         self.assertFalse(pickMock.called)

#     @patch('euchre.objects.Table.updateScore')
#     def scoreTests(self, tricks0, tricks1, maker, loner, winner, points,
#                    USMock):
#         if tricks0 + tricks1 != 5:
#             raise ValueError("Bad test - not five tricks")
#         self.h.tricksTaken = {0: tricks0, 1: tricks1}
#         self.h.maker = maker
#         self.h.loner = loner
#         self.h.scoreRound()
#         USMock.assert_called_once_with(winner, points)

#     def test_scoreRound(self):
#         tests = {(3, 2, 0, False, 0, 1),
#                  (2, 3, 0, False, 1, 2),
#                  (5, 0, 0, False, 0, 2),
#                  (0, 5, 0, False, 1, 2),
#                  (4, 1, 0, True, 0, 1),
#                  (5, 0, 0, True, 0, 4)
#                  }
#         for x in tests:
#             with self.subTest(x=x):
#                 self.scoreTests(*x)

#     @patch('euchre.objects.Table.itPlayers')
#     @patch('euchre.objects.Trick.play')
#     def test_playRound(self, playPatch, itPatch):
#         playPatch.side_effect = [self.t.players[n] for n in [2, 3, 0, 0, 1]]
#         self.h.configureRound(self.t.players[3], "C", False)
#         self.h.playRound()
#         self.assertEqual(3, self.h.tricksTaken[0])
#         self.assertEqual(2, self.h.tricksTaken[1])
#         itPatch.assert_has_calls([call(n, excluded={None})
#                                   for n in [1, 2, 3, 0, 0]])
