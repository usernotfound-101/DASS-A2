from dataclasses import dataclass
import os
import sys


if __package__ is None or __package__ == "":
    # Support direct script execution: python streetracemanager/system.py
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from streetracemanager.functionalities.betting import BettingSystem
from streetracemanager.functionalities.crew import CrewMems
from streetracemanager.functionalities.inventory import Inventory
from streetracemanager.functionalities.journalist import JournalistReportSystem
from streetracemanager.functionalities.mission import MissionPlanner
from streetracemanager.functionalities.race import RaceManager
from streetracemanager.functionalities.registration import People
from streetracemanager.functionalities.results import ResultsManager


@dataclass(slots=True)
class StreetRaceManagerApp:
    people: People
    crew: CrewMems
    inventory: Inventory
    races: RaceManager
    results: ResultsManager
    missions: MissionPlanner
    betting: BettingSystem
    journalist: JournalistReportSystem

    @classmethod
    def build(cls):
        people = People()
        crew = CrewMems(people)
        inventory = Inventory()
        races = RaceManager(crew, inventory)
        results = ResultsManager(races, inventory)
        missions = MissionPlanner(crew, inventory)
        betting = BettingSystem(races, inventory)
        journalist = JournalistReportSystem(results)
        return cls(people, crew, inventory, races, results, missions, betting, journalist)


def run_cli():
    app = StreetRaceManagerApp.build()
    print("StreetRace Manager CLI. Type 'help' for commands, 'exit' to quit.")

    while True:
        command = input("srm> ").strip()
        if not command:
            continue
        if command.lower() == "exit":
            print("Exiting StreetRace Manager.")
            break
        if command.lower() == "help":
            print("register <name>")
            print("assign-role <name> <role> <skill>")
            print("add-vehicle <vehicle_id> <vehicle_type>")
            print("create-race <race_id> <vehicle_id> <distance_km> <driver_name...>")
            print("record-result <race_id> <winner_name> <prize_money> <damage_taken>")
            print("plan-mission <mission_id> <mission_type> <required_role...>")
            print("place-bet <race_id> <bettor> <predicted_winner> <amount>")
            print("settle-bets <race_id>")
            print("publish-report <race_id>")
            print("cash")
            continue

        try:
            parts = command.split()
            action = parts[0].lower()

            if action == "register" and len(parts) == 2:
                person = app.people.register(parts[1])
                print(f"Registered {person.name}")
            elif action == "assign-role" and len(parts) == 4:
                crew_member = app.crew.assign(parts[2], int(parts[3]), parts[1])
                print(f"Assigned {crew_member.crewtype} to {crew_member.person_info.name}")
            elif action == "add-vehicle" and len(parts) == 3:
                vehicle = app.inventory.add_vehicle(parts[1], parts[2])
                print(f"Vehicle {vehicle.vehicle_id} added")
            elif action == "create-race" and len(parts) >= 5:
                race = app.races.create_race(parts[1], parts[4:], parts[2], float(parts[3]))
                print(f"Race created: {race.race_id}")
            elif action == "record-result" and len(parts) == 5:
                result = app.results.record_race_result(
                    parts[1],
                    parts[2],
                    float(parts[3]),
                    int(parts[4]),
                )
                print(f"Recorded result for race {result['race_id']}")
            elif action == "plan-mission" and len(parts) >= 4:
                mission = app.missions.plan_mission(parts[1], parts[2], parts[3:])
                print(f"Mission started: {mission.mission_id}")
            elif action == "place-bet" and len(parts) == 5:
                app.betting.place_bet(parts[1], parts[2], parts[3], float(parts[4]))
                print("Bet placed")
            elif action == "settle-bets" and len(parts) == 2:
                payouts = app.betting.settle_race_bets(parts[1])
                print(f"Payouts: {payouts}")
            elif action == "publish-report" and len(parts) == 2:
                story = app.journalist.publish_race_report(parts[1])
                print(story)
            elif action == "cash" and len(parts) == 1:
                print(f"Cash balance: {app.inventory.cash_balance:.2f}")
            else:
                print("Unknown or malformed command. Use 'help'.")

        except ValueError as err:
            print(f"Error: {err}")


if __name__ == "__main__":
    run_cli()
