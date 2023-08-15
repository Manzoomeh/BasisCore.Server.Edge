from ..answer.enriched_data import EnrichedData

class QuestionData:
    def __init__(self, prpid:"int", typeid:"int|None", wordid:"int|None", enriched_data:"list[EnrichedData]") -> None:
        self.prpid = prpid
        self.typeid = typeid
        self.wordid = wordid
        self.enriched_data = enriched_data