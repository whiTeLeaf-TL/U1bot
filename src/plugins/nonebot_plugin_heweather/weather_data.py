import asyncio
from typing import Optional, Union

from httpx import AsyncClient, Response
from nonebot.log import logger

from .model import AirApi, DailyApi, HourlyApi, NowApi, WarningApi


class APIError(Exception):
    ...


class ConfigError(Exception):
    ...


class CityNotFoundError(Exception):
    ...


class Weather:
    def __url__(self):
        if self.api_type == 2:
            self.url_weather_api = "https://api.qweather.com/v7/weather/"
            self.url_geoapi = "https://geoapi.qweather.com/v2/city/"
            self.url_weather_warning = "https://api.qweather.com/v7/warning/now"
            self.url_air = "https://api.qweather.com/v7/air/now"
            self.url_hourly = "https://api.qweather.com/v7/weather/24h"
            self.forecast_days = 7
            logger.info("使用商业版 API")
        elif self.api_type in [0, 1]:
            self.url_weather_api = "https://devapi.qweather.com/v7/weather/"
            self.url_geoapi = "https://geoapi.qweather.com/v2/city/"
            self.url_weather_warning = "https://devapi.qweather.com/v7/warning/now"
            self.url_air = "https://devapi.qweather.com/v7/air/now"
            self.url_hourly = "https://devapi.qweather.com/v7/weather/24h"
            if self.api_type == 0:
                self.forecast_days = 3
                logger.info("使用普通版 API")
            else:
                self.forecast_days = 7
                logger.info("使用个人开发版 API")
        else:
            raise ConfigError(
                "api_type 必须是为 (int)0 -> 普通版，(int)1 -> 个人开发版，(int)2 -> 商业版"
                f"\n当前为：({type(self.api_type)}){self.api_type}"
            )

    def __init__(self, city_name: str, api_key: str, api_type: Union[int, str] = 0):
        self.city_name = city_name
        self.apikey = api_key
        self.api_type = int(api_type)
        self.__url__()

        self.__reference = "\n请参考：https://dev.qweather.com/docs/start/status-code/"
        self.city_id = None
        self.now = None
        self.daily = None
        self.air = None
        self.warning = None
        self.hourly = None

    async def load_data(self):
        self.city_id = await self._get_city_id()
        (
            self.now,
            self.daily,
            self.air,
            self.warning,
            self.hourly,
        ) = await asyncio.gather(
            self._now, self._daily, self._air, self._warning, self._hourly
        )
        self._data_validate()

    @staticmethod
    async def _get_data(url: str, params: dict) -> Response:
        async with AsyncClient() as client:
            res = await client.get(url, params=params)
        return res

    async def _get_city_id(self, api_type: str = "lookup"):
        res = await self._get_data(
            url=self.url_geoapi + api_type,
            params={"location": self.city_name, "key": self.apikey},
        )

        res = res.json()
        logger.debug(res)
        if res["code"] == "404":
            raise CityNotFoundError()
        if res["code"] != "200":
            raise APIError(f'错误！错误代码：{res["code"]}{self.__reference}')
        self.city_name = res["location"][0]["name"]
        return res["location"][0]["id"]

    def _data_validate(self):
        if self.now.code != "200" or self.daily.code != "200":
            raise APIError(
                f"错误！请检查配置！错误代码：now: {self.now.code}  daily: {self.daily.code}  "
                + f'air: {self.air.code if self.air else "None"}  '
                + f'warning: {self.warning.code if self.warning else "None"}'
                + self.__reference
            )

    @staticmethod
    def _check_response(response: Response) -> bool:
        if response.status_code != 200:
            raise APIError(f"Response code:{response.status_code}")
        logger.debug(f"{response.json()}")
        return True

    @property
    async def _now(self) -> NowApi:
        res = await self._get_data(
            url=f"{self.url_weather_api}now",
            params={"location": self.city_id, "key": self.apikey},
        )
        self._check_response(res)
        return NowApi(**res.json())

    @property
    async def _daily(self) -> DailyApi:
        res = await self._get_data(
            url=self.url_weather_api + str(self.forecast_days) + "d",
            params={"location": self.city_id, "key": self.apikey},
        )
        self._check_response(res)
        return DailyApi(**res.json())

    @property
    async def _air(self) -> AirApi:
        res = await self._get_data(
            url=self.url_air,
            params={"location": self.city_id, "key": self.apikey},
        )
        self._check_response(res)
        return AirApi(**res.json())

    @property
    async def _warning(self) -> Optional[WarningApi]:
        res = await self._get_data(
            url=self.url_weather_warning,
            params={"location": self.city_id, "key": self.apikey},
        )
        self._check_response(res)
        return None if res.json().get("code") == "204" else WarningApi(**res.json())

    @property
    async def _hourly(self) -> HourlyApi:
        res = await self._get_data(
            url=self.url_hourly,
            params={"location": self.city_id, "key": self.apikey},
        )
        return HourlyApi(**res.json())
