from dataclasses import dataclass


@dataclass(slots=True)
class Person:
    name: str
    role: str | None = None


class People:
    def __init__(self):
        self._registrars: dict[str, Person] = {}

    @property
    def registrars(self) -> list[Person]:
        return list(self._registrars.values())

    def register(self, name: str, role: str | None = None) -> Person:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Name cannot be empty")
        if normalized_name in self._registrars:
            raise ValueError(f"Person already registered: {normalized_name}")

        person = Person(normalized_name, role)
        self._registrars[normalized_name] = person
        return person

    def get_by_name(self, name: str) -> Person | None:
        return self._registrars.get(name.strip())
