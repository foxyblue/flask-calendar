from __future__ import annotations

import datetime
from enum import Enum

from decimal import Decimal

import msgspec


class TimePeriod(Enum):
    DayTime = "day_time"
    NightTime = "night_time"


class UVIndex(msgspec.Struct):
    index: Decimal
    time: datetime.time | None


class Datapoint(msgspec.Struct):
    # We need to include location
    n: int
    points: int
    min_temp: Decimal
    max_temp: Decimal
    max_humidity: int
    chance_of_rain: int
    sum_windspeed: Decimal
    max_windspeed: Decimal
    time_period: TimePeriod
    time_of_highest_uv: UVIndex

    @property
    def ave_windspeed(self):
        return Decimal(self.sum_windspeed / self.points).quantize(Decimal("0.01"))


class Weather:
    def __init__(self, dataset: list[Datapoint]):
        # Skip the first item, this is a night
        # item
        self.dataset = dataset[1:]
