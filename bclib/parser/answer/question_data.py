from bclib.parser.answer.enriched_data import EnrichedData


class QuestionData:
    def __init__(self, prpid: "int", ownerid: "int|None", typeid: "int|None", wordid: "int|None", enriched_data: "list[EnrichedData]") -> None:
        self.prpid = prpid
        self.ownerid = ownerid if ownerid is not None else 0
        self.typeid = typeid
        self.wordid = wordid
        self.enriched_data = enriched_data
