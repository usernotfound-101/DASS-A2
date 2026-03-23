import pytest

from streetracemanager.system import StreetRaceManagerApp


def _bootstrap_app_with_core_roles():
    app = StreetRaceManagerApp.build()
    app.people.register("Asha")
    app.people.register("Ravi")
    app.people.register("Mira")
    app.crew.assign("DRIVER", 90, "Asha")
    app.crew.assign("MECHANIC", 88, "Ravi")
    app.crew.assign("STRATEGIST", 80, "Mira")
    app.inventory.add_vehicle("car-01", "CAR")
    return app


def test_registration_before_role_assignment():
    app = StreetRaceManagerApp.build()
    with pytest.raises(ValueError, match="User not registered"):
        app.crew.assign("DRIVER", 75, "Unknown")


def test_register_driver_then_enter_race_successfully():
    app = StreetRaceManagerApp.build()
    app.people.register("Arjun")
    app.crew.assign("DRIVER", 91, "Arjun")
    app.inventory.add_vehicle("car-11", "CAR")

    race = app.races.create_race("R-11", ["Arjun"], "car-11", 4.2)

    assert race.race_id == "R-11"
    assert race.participants[0].person_info.name == "Arjun"


def test_enter_race_without_registered_driver_fails():
    app = StreetRaceManagerApp.build()
    app.inventory.add_vehicle("car-12", "CAR")

    with pytest.raises(ValueError, match="Participant is not a crew member"):
        app.races.create_race("R-12", ["GhostDriver"], "car-12", 3.0)


def test_only_driver_can_be_entered_in_race():
    app = StreetRaceManagerApp.build()
    app.people.register("Ira")
    app.crew.assign("MECHANIC", 70, "Ira")
    app.inventory.add_vehicle("car-02", "CAR")

    with pytest.raises(ValueError, match="Only drivers can race"):
        app.races.create_race("R-1", ["Ira"], "car-02", 3.5)


def test_race_results_update_cash_balance():
    app = _bootstrap_app_with_core_roles()
    app.races.create_race("R-1", ["Asha"], "car-01", 4.0)
    app.results.record_race_result("R-1", "Asha", 1200.0, 0)

    assert app.inventory.cash_balance == 1200.0
    assert app.results.rankings["Asha"] == 1


def test_assign_mission_with_required_roles_successfully():
    app = _bootstrap_app_with_core_roles()

    mission = app.missions.plan_mission("M-5", "DELIVERY", ["DRIVER", "MECHANIC"])

    assert mission.status == "STARTED"
    assert mission.required_roles == ["DRIVER", "MECHANIC"]
    assert set(mission.assigned_members) == {"Asha", "Ravi"}


def test_mission_cannot_start_if_required_roles_unavailable():
    app = StreetRaceManagerApp.build()
    app.people.register("Solo")
    app.crew.assign("DRIVER", 77, "Solo")

    with pytest.raises(ValueError, match="role unavailable"):
        app.missions.plan_mission("M-1", "DELIVERY", ["DRIVER", "MECHANIC"])


def test_damaged_car_requires_mechanic_for_mission_flow():
    app = _bootstrap_app_with_core_roles()
    app.races.create_race("R-2", ["Asha"], "car-01", 2.0)
    app.results.record_race_result("R-2", "Asha", 500.0, 25)

    assert app.missions.verify_mechanic_for_damaged_car("car-01") is True

    app_without_mech = StreetRaceManagerApp.build()
    app_without_mech.people.register("DriverOne")
    app_without_mech.crew.assign("DRIVER", 85, "DriverOne")
    app_without_mech.inventory.add_vehicle("car-09", "CAR")
    app_without_mech.races.create_race("R-9", ["DriverOne"], "car-09", 2.0)
    app_without_mech.results.record_race_result("R-9", "DriverOne", 450.0, 30)

    with pytest.raises(ValueError, match="requires an available mechanic"):
        app_without_mech.missions.verify_mechanic_for_damaged_car("car-09")


def test_betting_system_and_journalist_reporting_modules():
    app = _bootstrap_app_with_core_roles()
    app.races.create_race("R-3", ["Asha"], "car-01", 5.0)

    app.betting.place_bet("R-3", "FanOne", "Asha", 100.0)
    app.betting.place_bet("R-3", "FanTwo", "Ghost", 100.0)

    app.results.record_race_result("R-3", "Asha", 800.0, 5)
    payouts = app.betting.settle_race_bets("R-3")

    assert payouts["FanOne"] == 180.0
    assert app.inventory.cash_balance == 820.0

    story = app.journalist.publish_race_report("R-3")
    assert "Race R-3 won by Asha" in story
    assert "Prize: 800.00" in story
