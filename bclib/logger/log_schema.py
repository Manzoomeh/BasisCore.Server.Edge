from typing import Any


class LogSchema:
    def __init__(self, schema: 'dict[str,Any]') -> None:
        self.schema_name = schema["schemaName"]
        self.schema_version = schema["schemaVersion"]
        self.lid = schema["lid"]
        self.schemaId = schema["schemaId"]
        self.paramUrl = schema["paramUrl"]
        self.properties: 'dict[str,(int,str)]' = dict([
            (x["title"], (x["prpId"], x["TypeID"] if "TypeID" in x else 0, x["source"] if "source" in x else None)) for x in schema["questions"]])

    def get_answer(self, params: 'dict[str,Any]'):
        properties = list()
        for key, (id, typeid, source) in self.properties.items():
            value = None
            try:
                if source:
                    value = eval(source, {}, params)
                else:
                    value = params[key] if key in params else None
            except:
                pass

            if value is not None:
                properties.append({
                    "prpId": id,
                    "TypeID": typeid,
                    "answers": [
                        {
                            "parts": [
                                {
                                    "part": 1,
                                    "values": [
                                        {
                                            "value": value
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                })
        return {
            "schemaName": self.schema_name,
            "paramUrl": self.paramUrl,
            "schemaVersion": self.schema_version,
            "lid": self.lid,
            "schemaId": self.schemaId,
            "properties": properties
        }
