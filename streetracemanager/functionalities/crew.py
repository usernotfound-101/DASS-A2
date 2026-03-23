from .config import CREW_TYPES
from .registration import People


class CrewMember:
    def __init__(self, crewtype, skill, person_info):
        self.crewtype = crewtype
        self.skill = skill
        self.person_info = person_info

    def validate_crew(self):
        if self.crewtype not in CREW_TYPES:
            raise ValueError(f"Expected a valid crew type, got {self.crewtype}")
        if self.skill < 0 or self.skill > 100:
            raise ValueError("Skill can only be between 0 and 100")


class CrewMems:
    def __init__(self, registrants=None):
        self.registrants = registrants or People()
        self.crewinfo = []

    def assign(self, crewtype, skill, name):
        person_info = self.registrants.get_by_name(name)
        if person_info is None:
            raise ValueError("User not registered")

        existing = self.get_by_name(name)
        if existing is not None:
            raise ValueError(f"Crew role already assigned for {name}")

        crew = CrewMember(crewtype.strip().upper(), int(skill), person_info)
        crew.validate_crew()
        person_info.role = crew.crewtype

        self.crewinfo.append(crew)
        return crew

    def get_by_name(self, name):
        for crew_member in self.crewinfo:
            if crew_member.person_info.name == name:
                return crew_member
        return None

    def members_with_role(self, role):
        normalized_role = role.strip().upper()
        return [member for member in self.crewinfo if member.crewtype == normalized_role]

    def ask_assign(self):
        name, crewtype, skill = input("Enter name crewtype and skill space separated").split()
        self.assign(crewtype, int(skill), name)

