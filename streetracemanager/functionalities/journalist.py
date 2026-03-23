from dataclasses import dataclass, field

from .results import ResultsManager


@dataclass(slots=True)
class JournalistReportSystem:
    results_manager: ResultsManager
    stories: list[str] = field(default_factory=list)

    def publish_race_report(self, race_id):
        result = None
        for entry in self.results_manager.history:
            if entry["race_id"] == race_id.strip().upper():
                result = entry
                break

        if result is None:
            raise ValueError(f"No result found for race: {race_id}")

        story = (
            f"Race {result['race_id']} won by {result['winner']}. "
            f"Prize: {result['prize_money']:.2f}. "
            f"Vehicle damage: {result['damage_taken']}."
        )
        self.stories.append(story)
        return story

    def rankings_digest(self):
        board = self.results_manager.leaderboard()
        if not board:
            return "No race records available."
        return " | ".join(f"{name}:{wins}" for name, wins in board)
