class TimeUserAction:

    def __init__(self, prp_id: "int", prp_value_id: "int", value_id: "int", time_value: "str", time_id: "int") -> None:
        self.prp_id = prp_id
        self.prp_value_id = prp_value_id
        self.value_id = value_id
        self.time_value = time_value
        self.time_id = time_id

    def as_tuple(self) -> tuple:
        return (self.prp_id, self.prp_value_id, self.value_id, self.time_value, self.time_id)

    def as_dict(self) -> dict:
        return {
            "prp_id": self.prp_id,
            "prp_value_id": self.prp_value_id,
            "value_id": self.value_id,
            "time_value": self.time_value,
            "time_id": self.time_id
        }

    def __str__(self) -> str:
        return str(self.as_tuple())

    def __repr__(self) -> str:
        return str(self.as_dict())
