# StreetRace Manager Integration Report

## 1. Module Responsibilities

1. Registration module
- Registers people by name and stores role assignment state.

2. Crew Management module
- Assigns crew roles (DRIVER, MECHANIC, STRATEGIST, ENGINEER).
- Stores and validates skill levels (0 to 100).
- Enforces that a person must be registered before role assignment.

3. Inventory module
- Tracks vehicles, spare parts, tools, and cash balance.
- Tracks vehicle availability and condition.

4. Race Management module
- Creates races.
- Selects participants from crew members with DRIVER role only.
- Allocates and releases vehicles from inventory.

5. Results module
- Records race outcomes.
- Updates rankings.
- Adds prize money to inventory cash balance.
- Applies vehicle damage after races.

6. Mission Planning module
- Assigns missions with required crew roles.
- Prevents mission start when required roles are unavailable.
- Verifies mechanic availability before continuing damaged-car flow.

7. Additional module: Betting System
- Accepts bets for active races.
- Settles bets after race finish.
- Adds house cut to inventory cash balance.

8. Additional module: Journalist Reporting System
- Builds race reports from recorded race results.
- Generates a rankings digest from leaderboard data.

## 2.1 Call Graph (Hand-Draw Guide)

Draw one node per function and connect arrows using the exact call list below.
Use different colors for each module, and highlight cross-module arrows.

### Registration module
- People.register
- People.get_by_name

### Crew module
- CrewMems.assign -> People.get_by_name
- CrewMems.assign -> CrewMember.validate_crew
- CrewMems.assign -> CrewMems.get_by_name
- CrewMems.members_with_role

### Inventory module
- Inventory.allocate_vehicle -> Inventory._require_vehicle
- Inventory.release_vehicle -> Inventory._require_vehicle
- Inventory.report_damage -> Inventory._require_vehicle
- Inventory._require_vehicle -> Inventory.get_vehicle
- Inventory.add_spare_parts -> Inventory._add_item
- Inventory.consume_spare_parts -> Inventory._consume_item
- Inventory.add_tools -> Inventory._add_item
- Inventory.consume_tools -> Inventory._consume_item

### Race module
- RaceManager.create_race -> CrewMems.get_by_name
- RaceManager.create_race -> Inventory.allocate_vehicle
- RaceManager.finish_race -> RaceManager.get_race
- RaceManager.finish_race -> Inventory.report_damage
- RaceManager.finish_race -> Inventory.release_vehicle

### Results module
- ResultsManager.record_race_result -> RaceManager.finish_race
- ResultsManager.record_race_result -> Inventory.add_cash
- ResultsManager.leaderboard

### Mission module
- MissionPlanner.plan_mission -> CrewMems.members_with_role
- MissionPlanner.verify_mechanic_for_damaged_car -> Inventory.get_vehicle
- MissionPlanner.verify_mechanic_for_damaged_car -> CrewMems.members_with_role

### Betting module
- BettingSystem.place_bet -> RaceManager.get_race
- BettingSystem.settle_race_bets -> RaceManager.get_race
- BettingSystem.settle_race_bets -> Inventory.add_cash

### Journalist module
- JournalistReportSystem.publish_race_report
- JournalistReportSystem.rankings_digest -> ResultsManager.leaderboard

### System orchestration module
- StreetRaceManagerApp.build -> constructor calls for all managers
- run_cli -> People.register
- run_cli -> CrewMems.assign
- run_cli -> Inventory.add_vehicle
- run_cli -> RaceManager.create_race
- run_cli -> ResultsManager.record_race_result
- run_cli -> MissionPlanner.plan_mission
- run_cli -> BettingSystem.place_bet
- run_cli -> BettingSystem.settle_race_bets
- run_cli -> JournalistReportSystem.publish_race_report

## 2.2 Integration Test Design

Execution command used:
- /home/ayush/DASS/dass-a2/.venv/bin/python -m pytest -q streetracemanager/tests

Run summary:
- 6 passed in 0.01s

### TC-01 Registered driver can enter race
- Scenario: Register a person, assign DRIVER role, add vehicle, then create race.
- Modules involved: Registration, Crew, Inventory, Race.
- Expected result: Race creation succeeds.
- Actual result after testing: Passed.
- Errors or logical issues found: None.
- Why this test is needed: Confirms normal business flow across multiple modules.

### TC-02 Race entry without valid driver role is blocked
- Scenario: Register person as MECHANIC and try to create race with that member.
- Modules involved: Registration, Crew, Race, Inventory.
- Expected result: System rejects participant with error about driver-only race access.
- Actual result after testing: Passed. Error raised as expected.
- Errors or logical issues found: None after fix.
- Why this test is needed: Prevents invalid participants from entering races.

### TC-03 Role assignment without registration is blocked
- Scenario: Assign a role to unknown person.
- Modules involved: Crew, Registration.
- Expected result: Assignment fails with registration error.
- Actual result after testing: Passed. Error raised as expected.
- Errors or logical issues found: None after fix.
- Why this test is needed: Enforces data integrity between registration and crew modules.

### TC-04 Race results update inventory cash and rankings
- Scenario: Complete a race and record prize money.
- Modules involved: Race, Results, Inventory.
- Expected result: Winner ranking increments and inventory cash increases by prize amount.
- Actual result after testing: Passed.
- Errors or logical issues found: None.
- Why this test is needed: Validates financial and ranking data flow after races.

### TC-05 Damaged car requires mechanic availability
- Scenario: Complete race with vehicle damage; verify mission flow requires mechanic.
- Modules involved: Race, Results, Inventory, Crew, Mission.
- Expected result: Verification succeeds when mechanic exists and fails when mechanic is unavailable.
- Actual result after testing: Passed in both positive and negative branches.
- Errors or logical issues found: None after fix.
- Why this test is needed: Validates a key safety dependency across mission and race outcomes.

### TC-06 Betting and journalist modules integrate with results flow
- Scenario: Place bets before race completion, record result, settle bets, publish report.
- Modules involved: Race, Results, Inventory, Betting, Journalist.
- Expected result: Correct payout map, house cut added to cash, and report content generated from results history.
- Actual result after testing: Passed.
- Errors or logical issues found: None.
- Why this test is needed: Proves added modules are integrated into core system lifecycle.

## 3. Issues Found and Fixed During Integration

1. Direct script execution import issue
- Issue: Running streetracemanager/system.py directly caused ModuleNotFoundError for package imports.
- Fix: Added package bootstrap logic and package initialization files.
- Impact: Both execution styles now work.

2. Incomplete original skeleton modules
- Issue: Initial files had missing logic and invalid references.
- Fix: Replaced with validated implementations and module interactions.
- Impact: Full integration behavior now available and testable.
