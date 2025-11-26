from typing import Any, Dict, List, Tuple


class LogSchema:
    """
    Log Schema Definition

    Represents a logging schema with metadata and property definitions.
    Converts log object properties into structured schema format for
    submission to logging backends.

    The schema defines:
        - Schema metadata (name, version, IDs)
        - Property definitions with types and constraints
        - Support for multi-part and multi-value properties
        - Dynamic value calculation via source expressions

    Attributes:
        schema_name (str): Schema name
        schema_version: Schema version
        lid: Log ID
        schemaId: Schema identifier
        paramUrl: Parameter URL
        properties (Dict[str, Tuple]): Property definitions mapping
            - Key: Property title
            - Value: (prpId, multi, parts_count, TypeID, source)

    Example:
        ```python
        # Schema loaded from API
        schema = LogSchema(schema_data)
        # Convert log properties to schema format
        formatted = schema.get_answer(log_object.properties)
        ```
    """

    def __init__(self, schema: Dict[str, Any]) -> None:
        """
        Initialize log schema from schema definition

        Args:
            schema: Schema definition dictionary containing:
                - schemaName: Name of the schema
                - schemaVersion: Version number
                - lid: Log ID
                - schemaId: Schema identifier
                - paramUrl: Parameter URL
                - questions: List of property definitions
        """
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
        """
        Convert log properties to schema-formatted answer

        Processes raw log properties according to schema definitions,
        handling multi-value properties, multi-part answers, and
        dynamic source expressions.

        Args:
            params: Dictionary of property names to nested value lists

        Returns:
            dict: Formatted schema answer with:
                - schemaName: Schema name
                - paramUrl: Parameter URL
                - schemaVersion: Schema version
                - lid: Log ID
                - schemaId: Schema ID
                - properties: List of formatted property answers

        Note:
            - Properties with source expressions are evaluated dynamically
            - Multi-value properties controlled by 'multi' flag
            - Parts are limited by 'parts_count'
            - Missing or error properties are silently skipped
        """
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
