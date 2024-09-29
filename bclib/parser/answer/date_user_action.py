class DateUserAction:

    def __init__(self, prp_id: "int", prp_value_id: "int", value_id: "int", mstring: "str", sstring: "str", date_id: "int") -> None:
        self.prp_id = prp_id
        self.prp_value_id = prp_value_id
        self.value_id = value_id
        self.mstring = mstring
        self.sstring = sstring
        self.date_id = date_id

    def as_tuple(self) -> tuple:
        return (self.prp_id, self.prp_value_id, self.value_id, self.mstring, self.sstring, self.date_id)

    def as_dict(self) -> dict:
        return {
            "prp_id": self.prp_id,
            "prp_value_id": self.prp_value_id,
            "value_id": self.value_id,
            "mstring": self.mstring,
            "sstring": self.sstring,
            "date_id": self.date_id
        }

    def __str__(self) -> str:
        return str(self.as_tuple())

    def __repr__(self) -> str:
        return str(self.as_dict())
