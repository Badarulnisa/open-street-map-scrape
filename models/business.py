from dataclasses import dataclass


@dataclass
class Business:
    name: str
    city: str
    area: str
    source: str

    def to_dict(self):
        return {
            "Company Name": self.name,
            "City": self.city,
            "Area": self.area,
            "Source": self.source
        }