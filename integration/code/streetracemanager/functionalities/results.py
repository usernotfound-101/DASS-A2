from dataclasses import dataclass, field

from .inventory import Inventory
from .race import RaceManager


@dataclass(slots=True)
class ResultsManager:
	race_manager: RaceManager
	inventory: Inventory
	rankings: dict[str, int] = field(default_factory=dict)
	history: list[dict] = field(default_factory=list)

	def record_race_result(self, race_id, winner_name, prize_money, damage_taken=0):
		race = self.race_manager.finish_race(
			race_id=race_id,
			winner_name=winner_name,
			prize_money=prize_money,
			damage_taken=damage_taken,
		)
		self.rankings[winner_name] = self.rankings.get(winner_name, 0) + 1
		self.inventory.add_cash(prize_money)

		result = {
			"race_id": race.race_id,
			"winner": winner_name,
			"prize_money": float(prize_money),
			"damage_taken": int(damage_taken),
		}
		self.history.append(result)
		return result

	def leaderboard(self):
		return sorted(self.rankings.items(), key=lambda item: (-item[1], item[0]))
