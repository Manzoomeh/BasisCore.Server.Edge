from abc import ABC, abstractmethod

import traceback
from typing import Optional
from bclib.utility import DictEx
from .log_object import LogObject

class ILogger(ABC):
    """Base class for logger"""

    def __init__(self,options:'DictEx'):
        self.options = options
        self.name = options["name"] if options.has("name") else None
        self.__log_name = f"{self.name}: " if self.name else ''
        self._log_error: bool = self.options.log_error if self.options.has(
            "log_error") else False
        self.__log_request: bool = self.options.log_request if self.options.has(
            "log_request") else True
        print(f'{self.__class__.__name__} start logging')
        

    @abstractmethod
    async def log_async(self, log_object: LogObject):
        """log data async"""

    def new_object_log(self, schema_name: str, routing_key: Optional[str] = None, **kwargs) -> LogObject:
        """New object log"""
        return LogObject(schema_name, routing_key, **kwargs)
    
    def log_request(self, message:'str'):
        if(self.__log_request):
            print(self.__log_name,'LOG', message)

    def log_error(self,error:'Exception'):
        print(self.__log_name,'ERROR',str(error))
        traceback.print_exc()

