from enum import Enum


class Tier(str, Enum):
    TEMP = "temp"
    HOT = "hot"
    COLD = "cold"
