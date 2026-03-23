from dataclasses import dataclass, field

from .crew import CrewMems
from .inventory import Inventory, Vehicle


@dataclass(slots=True)
class Race:
    race_id: str
    participants: list
    vehicle: Vehicle
    distance_km: float
    winner_name: str | None = None
    prize_money: float = 0.0
    damage_taken: int = 0
    finished: bool = False

    def validate_race(self):
        for racer in self.participants:
            if racer.crewtype != "DRIVER":
                return False
        return True


@dataclass(slots=True)
class RaceManager:
    crew_manager: CrewMems
    inventory: Inventory
    races: dict[str, Race] = field(default_factory=dict)

    def create_race(self, race_id, participant_names, vehicle_id, distance_km):
        normalized_race_id = race_id.strip().upper()
        if normalized_race_id in self.races:
            raise ValueError(f"Race already exists: {normalized_race_id}")

        participants = []
        for name in participant_names:
            crew_member = self.crew_manager.get_by_name(name)
            if crew_member is None:
                raise ValueError(f"Participant is not a crew member: {name}")
            if crew_member.crewtype != "DRIVER":
                raise ValueError(f"Only drivers can race: {name}")
            participants.append(crew_member)

        vehicle = self.inventory.allocate_vehicle(vehicle_id)
        race = Race(
            race_id=normalized_race_id,
            participants=participants,
            vehicle=vehicle,
            distance_km=float(distance_km),
        )
        self.races[normalized_race_id] = race
        return race

    def finish_race(self, race_id, winner_name, prize_money, damage_taken=0):
        race = self.get_race(race_id)
        if race.finished:
            raise ValueError(f"Race already finished: {race.race_id}")

        participant_names = {member.person_info.name for member in race.participants}
        if winner_name not in participant_names:
            raise ValueError("Winner must be a race participant")

        race.winner_name = winner_name
        race.prize_money = float(prize_money)
        race.damage_taken = int(damage_taken)
        race.finished = True
        if race.damage_taken > 0:
            self.inventory.report_damage(race.vehicle.vehicle_id, race.damage_taken)
        self.inventory.release_vehicle(race.vehicle.vehicle_id)
        return race

    def get_race(self, race_id):
        normalized_race_id = race_id.strip().upper()
        race = self.races.get(normalized_race_id)
        if race is None:
            raise ValueError(f"Unknown race: {race_id}")
        return race


class Races(RaceManager):
    pass
