class FileUserAction:

    def __init__(self, prp_id: "int", prp_value_id: "int", value_id: "int", name: "str", type: "str", size: "int", content: "str", upload_token:"str|None") -> None:
        self.prp_id = prp_id
        self.prp_value_id = prp_value_id
        self.value_id = value_id
        self.name = name
        self.type = type
        self.size = size
        self.content = content
        self.is_blob = upload_token is not None


    def as_tuple(self) -> tuple:
        return (self.prp_id, self.prp_value_id, self.value_id, self.name, self.type, self.size, self.content)

    def as_dict(self) -> dict:
        return {
            "prp_id": self.prp_id,
            "prp_value_id": self.prp_value_id,
            "value_id": self.value_id,
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "content": self.content
        }

    def __str__(self) -> str:
        return str(self.as_tuple())

    def __repr__(self) -> str:
        return str(self.as_dict())
