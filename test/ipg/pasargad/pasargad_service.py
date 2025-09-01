from abc import ABC, abstractmethod
from dataclasses import dataclass
import dataclasses
import json
from typing import Protocol
from urllib.parse import urljoin
import aiohttp
from dependency_injector.providers import ConfigurationOption
from dispatcher.routing_dispatcher import RoutingDispatcher
from utility.dict_ex import DictEx


@dataclass
class PurchaseResult:
    urlId: str
    url: str


@dataclass
class BaseResult():
    resultMsg: str
    resultCode: int


@dataclass
class GetTokenResult(BaseResult):
    token: str
    username: str
    firstName: str
    lastName: str
    userId: str
    roles: list


@dataclass
class PasargadIPGBaseException(Exception):
    pass


@dataclass
class PasargadApiCallError(PasargadIPGBaseException):
    httpStatusCode: str
    content: str


@dataclass
class PasargadApiResultError(PasargadIPGBaseException):
    resultMsg: str
    resultCode: int


class ResultCodes:
    OK = 0


class IPasargadService(ABC):
    @abstractmethod
    async def get_token_async(self) -> str:
        pass

    @abstractmethod
    async def purchase_async(self, invoice: str, amount: int, description: str | None) -> dict:
        pass


class PasargadService(IPasargadService):

    SERVICE_CODE = 8
    SERVICE_TYPE = "PURCHASE"

    def __init__(self, config: 'DictEx', dispatcher: 'RoutingDispatcher'):

        self.username: str = config["username"]
        self.password: str = config["password"]
        self.base_url: str = config["base_url"]
        self.terminalid: str = config["terminalid"]
        self.dispatcher = dispatcher

    @staticmethod
    async def post_request_async(url: str, payload: dict, token: str | None = None) -> dict:
        ret_val: BaseResult
        async with aiohttp.ClientSession() as session:
            headers = {
                'Content-Type': 'application/json'
            }
            if token != None:
                headers['Authorization'] = f'Bearer {token}'
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise PasargadApiCallError(
                        response.status, response.text())

    async def get_token_async(self) -> GetTokenResult:
        url = urljoin(self.base_url, '/token/getToken')
        payload = {"username": self.username, "password": self.password}
        result = await PasargadService.post_request_async(url, payload)
        resultCode = result["resultCode"]
        print("Response:", resultCode)
        if resultCode == ResultCodes.OK:
            print("ok")
            return GetTokenResult(**result)
        else:
            print("error")
            raise PasargadApiResultError(result["resultMsg"], resultCode)

    async def purchase_async(self, invoice: str, amount: int, description: str | None = None) -> PurchaseResult:
        invoiceDate = ""
        request = PurchaseRequest(
            invoice,
            invoiceDate,
            amount,
            "callbackApi",
            None,
            PasargadService.SERVICE_CODE,
            PasargadService.SERVICE_TYPE,
            self.terminalid,
            description,
            None,
            None,
            None,
            None)
        url = urljoin(self.base_url, '/api/payment/purchase')
        token = "sdsdsdsd"
        result = await PasargadService.post_request_async(url, dataclasses.asdict(request), token)
        resultCode = result["resultCode"]
        print("Response:", resultCode)
        if resultCode == ResultCodes.OK:
            return PurchaseResult(result["data"]["urlId"], result["data"]["url"])
        else:
            print("error")
            raise PasargadApiResultError(result["resultMsg"], resultCode)


@dataclass
class PurchaseRequest:
    invoice: str
    invoiceDate: str
    amount: int
    callbackApi: str
    mobileNumber: str | None
    serviceCode: str
    serviceType: str
    terminalNumber: int
    description: str | None
    payerMail: str | None
    payerName: str | None
    pans: str | None
    nationalCode: str | None
