import unittest
from unittest.mock import patch

from moneypoly.bank import Bank
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property


class TestWhiteBoxCases(unittest.TestCase):
    def setUp(self):
        self.game = Game(["A", "B"])
        self.a = self.game.players[0]
        self.b = self.game.players[1]

    def test_dice_roll_includes_upper_bound_six(self):
        def fake_randint(low, high):
            self.assertEqual(low, 1)
            self.assertEqual(high, 6)
            return 6

        with patch("random.randint", side_effect=fake_randint):
            roll = self.game.dice.roll()
        self.assertEqual(roll, 12)

    def test_player_move_passing_go_awards_salary(self):
        p = Player("Mover", balance=1000)
        p.position = 39
        p.move(2)
        self.assertEqual(p.position, 1)
        self.assertEqual(p.balance, 1200)

    def test_buy_property_with_exact_balance_succeeds(self):
        p = Player("Buyer", balance=200)
        prop = Property("Cheap", 1, 200, 20)
        ok = self.game.buy_property(p, prop)
        self.assertTrue(ok)
        self.assertIs(prop.owner, p)
        self.assertEqual(p.balance, 0)

    def test_pay_rent_transfers_to_owner(self):
        tenant = Player("Tenant", balance=500)
        owner = Player("Owner", balance=300)
        prop = Property("RentProp", 3, 100, 50)
        prop.owner = owner

        self.game.pay_rent(tenant, prop)

        self.assertEqual(tenant.balance, 450)
        self.assertEqual(owner.balance, 350)

    def test_jail_fine_branch_deducts_player_balance(self):
        self.a.go_to_jail()
        start_player = self.a.balance
        start_bank = self.game.bank.get_balance()

        with patch("moneypoly.ui.confirm", side_effect=[True]), patch.object(
            self.game.dice, "roll", return_value=1
        ), patch.object(self.game.board, "get_tile_type", return_value="blank"):
            self.game._handle_jail_turn(self.a)

        self.assertEqual(self.a.balance, start_player - 50)
        self.assertEqual(self.game.bank.get_balance(), start_bank + 50)
        self.assertFalse(self.a.in_jail)

    def test_find_winner_returns_highest_net_worth(self):
        self.a.balance = 1200
        self.b.balance = 1700
        winner = self.game.find_winner()
        self.assertIs(winner, self.b)

    def test_bank_collect_negative_amount_is_ignored(self):
        bank = Bank()
        before = bank.get_balance()
        bank.collect(-100)
        self.assertEqual(bank.get_balance(), before)

    def test_bank_give_loan_reduces_bank_funds(self):
        bank = Bank()
        p = Player("Loaner", balance=100)
        start_bank = bank.get_balance()
        bank.give_loan(p, 60)
        self.assertEqual(p.balance, 160)
        self.assertEqual(bank.get_balance(), start_bank - 60)


if __name__ == "__main__":
    unittest.main()
