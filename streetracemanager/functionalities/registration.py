class Person:

    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender

class People:

    def __init__(self):
        self.registrars = []

    def register(self, name, age, gender):
        this_guy = Person(name, age, gender)
        self.registrars.append(this_guy)
        return this_guy

    def get_by_name(self, name):
        for registrant in self.registrars:
            if registrant.name == name:
                return registrant
        return None
