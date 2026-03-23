from dataclasses import dataclass

from .config import DEFAULT_CASH_BALANCE, VEHICLE_TYPES


@dataclass(slots=True)
class Vehicle:
	vehicle_id: str
	vehicle_type: str
	condition: int = 100
	available: bool = True


class Inventory:
	def __init__(self, cash_balance=DEFAULT_CASH_BALANCE):
		self.cars: dict[str, Vehicle] = {}
		self.spare_parts: dict[str, int] = {}
		self.tools: dict[str, int] = {}
		self.cash_balance = float(cash_balance)

	def add_vehicle(self, vehicle_id, vehicle_type):
		normalized_vehicle_id = vehicle_id.strip().upper()
		normalized_vehicle_type = vehicle_type.strip().upper()
		if normalized_vehicle_type not in VEHICLE_TYPES:
			raise ValueError(f"Unsupported vehicle type: {vehicle_type}")
		if normalized_vehicle_id in self.cars:
			raise ValueError(f"Vehicle already exists: {normalized_vehicle_id}")
		vehicle = Vehicle(normalized_vehicle_id, normalized_vehicle_type)
		self.cars[normalized_vehicle_id] = vehicle
		return vehicle

	def get_vehicle(self, vehicle_id):
		return self.cars.get(vehicle_id.strip().upper())

	def allocate_vehicle(self, vehicle_id):
		vehicle = self._require_vehicle(vehicle_id)
		if not vehicle.available:
			raise ValueError(f"Vehicle not available: {vehicle.vehicle_id}")
		if vehicle.condition <= 0:
			raise ValueError(f"Vehicle unusable: {vehicle.vehicle_id}")
		vehicle.available = False
		return vehicle

	def release_vehicle(self, vehicle_id):
		vehicle = self._require_vehicle(vehicle_id)
		vehicle.available = True

	def report_damage(self, vehicle_id, damage):
		vehicle = self._require_vehicle(vehicle_id)
		vehicle.condition = max(0, vehicle.condition - int(damage))
		return vehicle.condition

	def add_spare_parts(self, part_name, quantity):
		self._add_item(self.spare_parts, part_name, quantity)

	def consume_spare_parts(self, part_name, quantity):
		self._consume_item(self.spare_parts, part_name, quantity)

	def add_tools(self, tool_name, quantity):
		self._add_item(self.tools, tool_name, quantity)

	def consume_tools(self, tool_name, quantity):
		self._consume_item(self.tools, tool_name, quantity)

	def add_cash(self, amount):
		self.cash_balance += float(amount)
		return self.cash_balance

	def deduct_cash(self, amount):
		amount = float(amount)
		if amount > self.cash_balance:
			raise ValueError("Insufficient cash balance")
		self.cash_balance -= amount
		return self.cash_balance

	def _require_vehicle(self, vehicle_id):
		vehicle = self.get_vehicle(vehicle_id)
		if vehicle is None:
			raise ValueError(f"Unknown vehicle: {vehicle_id}")
		return vehicle

	@staticmethod
	def _add_item(bucket, name, quantity):
		quantity = int(quantity)
		if quantity <= 0:
			raise ValueError("Quantity must be positive")
		normalized_name = name.strip().lower()
		bucket[normalized_name] = bucket.get(normalized_name, 0) + quantity

	@staticmethod
	def _consume_item(bucket, name, quantity):
		quantity = int(quantity)
		if quantity <= 0:
			raise ValueError("Quantity must be positive")
		normalized_name = name.strip().lower()
		current = bucket.get(normalized_name, 0)
		if current < quantity:
			raise ValueError(f"Insufficient stock for {name}")
		bucket[normalized_name] = current - quantity
