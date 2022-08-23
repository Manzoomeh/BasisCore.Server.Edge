class StorageData:
    def __init__(self, data_base:"str", table:"str", field:"str") -> None:
        self.data_base = data_base
        self.table = table
        self.field = field