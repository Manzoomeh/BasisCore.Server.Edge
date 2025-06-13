from typing import Any, List, Dict, Tuple


class LogSchema:
    def __init__(self, schema: Dict[str, Any]) -> None:
        self.schema_name = schema["schemaName"]
        self.schema_version = schema["schemaVersion"]
        self.lid = schema["lid"]
        self.schemaId = schema["schemaId"]
        self.paramUrl = schema["paramUrl"]
        self.properties: Dict[str, Tuple[int, bool, int, int, str]] = dict(
            [
                (
                    q["title"], (
                        q["prpId"],
                        bool(q.get("multi", False)),
                        len(q["parts"]),
                        q["TypeID"] if "TypeID" in q else 0,
                        q["source"] if "source" in q else None
                    )
                )
                for q in schema["questions"]
            ]
        )

    def get_answer(self, params: Dict[str, List[List]]):
        properties = list()
        for key, (id, multi, parts_count, typeid, source) in self.properties.items():
            try:
                if source is not None:
                    value = eval(source, {}, params)
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
                else:
                    if key in params:
                        values = params[key]
                        if not multi:
                            values = values[:1]
                        prp_answers = list()
                        for parts_val in values:
                            answer_parts = list()
                            part_index = 1
                            parts_val = parts_val[:parts_count]
                            for part_val in parts_val:
                                answer_parts.append({
                                    "part": part_index,
                                    "values": [
                                        {
                                            "value": part_val
                                        }
                                    ]
                                })
                                part_index += 1
                            prp_answers.append({
                                "parts": answer_parts
                            })
                        properties.append({
                            "prpId": id,
                            "TypeID": typeid,
                            "answers": prp_answers
                        })

            except:
                pass
        return {
            "schemaName": self.schema_name,
            "paramUrl": self.paramUrl,
            "schemaVersion": self.schema_version,
            "lid": self.lid,
            "schemaId": self.schemaId,
            "properties": properties
        }
