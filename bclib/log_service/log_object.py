from typing import Dict, List, Optional


class LogObject:
    """
    Log Object Container

    Encapsulates log data with schema information and properties. Stores
    log properties as key-value pairs where values can have multiple entries.

    Properties are stored in a nested list structure to support multiple
    values per property and multiple parts per value.

    Attributes:
        schema_name (str): Name of the log schema
        routingKey (Optional[str]): Routing key for message-based loggers
        properties (Dict[str, List[List]]): Dictionary of log properties

    Example:
        ```python
        log_obj = LogObject(
            "user_action",
            routing_key="users.activity",
            user_id=123,
            action="login"
        )
        log_obj.add_property("timestamp", ["2024-01-01T12:00:00"])
        ```
    """

    def __init__(self, schema_name: str, routing_key: Optional[str] = None, **kwargs) -> None:
        """
        Initialize log object

        Args:
            schema_name: Name of the log schema
            routing_key: Optional routing key for message-based logging
            **kwargs: Initial properties to add to the log
        """
        self.__items: Dict[str, List[List]] = dict()
        for key, value in kwargs.items():
            self.add_property(key, [value])
        self.schema_name = schema_name
        self.routingKey = routing_key

    def add_property(self, prp_title: str, answer: List):
        """
        Add a property to the log object

        Args:
            prp_title: Property name/title
            answer: List of values for this property

        Note:
            Properties with empty answer lists are ignored.
            Multiple calls with the same prp_title will append values.
        """
        if len(answer) > 0:
            if prp_title not in self.__items:
                self.__items[prp_title] = list()
            self.__items[prp_title].append(answer)

    @property
    def properties(self):
        """
        Get all log properties

        Returns:
            Dict[str, List[List]]: Dictionary of property names to nested value lists
        """
        return self.__items
