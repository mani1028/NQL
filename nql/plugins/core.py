from typing import List, Dict

class NQLPlugin:
    def __init__(self, name: str, synonyms: Dict[str, List[str]]):
        self.name = name
        self.synonyms = synonyms

class SchoolERPPlugin(NQLPlugin):
    def __init__(self):
        super().__init__(
            name="SchoolERP",
            synonyms={
                "student": ["pupil", "learner", "scholar"],
                "fee": ["payment", "dues", "tuition"],
                "attendance": ["presence", "absent", "present"]
            }
        )

class HRMSPlugin(NQLPlugin):
    def __init__(self):
        super().__init__(
            name="HRMS",
            synonyms={
                "employee": ["staff", "worker", "colleague"],
                "salary": ["pay", "wage", "compensation"],
                "leave": ["time off", "vacation", "sick leave"]
            }
        )

class InventoryPlugin(NQLPlugin):
    def __init__(self):
        super().__init__(
            name="Inventory",
            synonyms={
                "product": ["item", "goods", "merchandise"],
                "warehouse": ["storage", "depot"],
                "stock": ["inventory", "quantity"]
            }
        )

class HospitalPlugin(NQLPlugin):
    def __init__(self):
        super().__init__(
            name="Hospital",
            synonyms={
                "patient": ["sick", "inmate", "case"],
                "doctor": ["physician", "surgeon", "medic"],
                "appointment": ["visit", "checkup", "consultation"]
            }
        )
