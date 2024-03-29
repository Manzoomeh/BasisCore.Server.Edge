from bclib.parser.answer.storage_data import StorageData


class EnrichedData:
    def __init__(self, part_number:"int", data_type:"str", storage_data:"StorageData|None", validators:"dict") -> None:
        self.part = part_number
        self.data_type = data_type
        self.storage_data = storage_data
        self.validators = validators