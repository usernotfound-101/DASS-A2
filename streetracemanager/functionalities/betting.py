from dataclasses import dataclass, field

from .inventory import Inventory
from .race import RaceManager


@dataclass(slots=True)
class Bet:
    race_id: str
    bettor: str
    predicted_winner: str
    amount: float


@dataclass(slots=True)
class BettingSystem:
    race_manager: RaceManager
    inventory: Inventory
    house_cut_ratio: float = 0.1
    bets: list[Bet] = field(default_factory=list)

    def place_bet(self, race_id, bettor, predicted_winner, amount):
        race = self.race_manager.get_race(race_id)
        if race.finished:
            raise ValueError("Cannot place bet on finished race")

        amount = float(amount)
        if amount <= 0:
            raise ValueError("Bet amount must be positive")

        self.bets.append(
            Bet(
                race_id=race.race_id,
                bettor=bettor.strip(),
                predicted_winner=predicted_winner.strip(),
                amount=amount,
            )
        )

    def settle_race_bets(self, race_id):
        race = self.race_manager.get_race(race_id)
        if not race.finished:
            raise ValueError("Race must be finished before settling bets")

        race_bets = [bet for bet in self.bets if bet.race_id == race.race_id]
        pool = sum(bet.amount for bet in race_bets)
        winners = [bet for bet in race_bets if bet.predicted_winner == race.winner_name]

        if not race_bets:
            return {}

        if not winners:
            self.inventory.add_cash(pool)
            return {}

        distributable = pool * (1.0 - self.house_cut_ratio)
        self.inventory.add_cash(pool - distributable)

        total_winner_amount = sum(winner.amount for winner in winners)
        payouts = {}
        for winner in winners:
            ratio = winner.amount / total_winner_amount
            payout = distributable * ratio
            payouts[winner.bettor] = round(payout, 2)
        return payouts
