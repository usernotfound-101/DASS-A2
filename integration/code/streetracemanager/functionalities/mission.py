from dataclasses import dataclass, field

from .config import MISSION_TYPES
from .crew import CrewMems
from .inventory import Inventory


@dataclass(slots=True)
class Mission:
	mission_id: str
	mission_type: str
	required_roles: list[str]
	assigned_members: list[str]
	status: str = "PLANNED"


@dataclass(slots=True)
class MissionPlanner:
	crew_manager: CrewMems
	inventory: Inventory
	missions: dict[str, Mission] = field(default_factory=dict)

	def plan_mission(self, mission_id, mission_type, required_roles):
		normalized_mission_id = mission_id.strip().upper()
		normalized_mission_type = mission_type.strip().upper()
		normalized_roles = [role.strip().upper() for role in required_roles]

		if normalized_mission_type not in MISSION_TYPES:
			raise ValueError(f"Unsupported mission type: {mission_type}")
		if normalized_mission_id in self.missions:
			raise ValueError(f"Mission already exists: {normalized_mission_id}")

		assigned_members = []
		for role in normalized_roles:
			members = self.crew_manager.members_with_role(role)
			if not members:
				raise ValueError(f"Mission cannot start, role unavailable: {role}")
			assigned_members.append(members[0].person_info.name)

		mission = Mission(
			mission_id=normalized_mission_id,
			mission_type=normalized_mission_type,
			required_roles=normalized_roles,
			assigned_members=assigned_members,
			status="STARTED",
		)
		self.missions[normalized_mission_id] = mission
		return mission

	def verify_mechanic_for_damaged_car(self, vehicle_id):
		vehicle = self.inventory.get_vehicle(vehicle_id)
		if vehicle is None:
			raise ValueError(f"Unknown vehicle: {vehicle_id}")
		if vehicle.condition < 100 and not self.crew_manager.members_with_role("MECHANIC"):
			raise ValueError("Damaged vehicle requires an available mechanic")
		return True
