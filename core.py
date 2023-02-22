#!/usr/bin/env python3
import os, json
from enum import Enum, auto
from decimal import Decimal
from loguru import logger
from typing import Dict

class Fiat(Enum):
    USD = auto()
    EUR = auto()
    RUB = auto()
    def from_xmr(self, amt: Decimal = 1) -> Decimal:
        return Fiat.course[self] * amt
    def to_xmr(self, amt: Decimal = 1) -> Decimal:
        return 1 / self.from_xmr(amt)

class FiatDict(dict):
    def __setitem__(self, k, v):
        if isinstance(k, Fiat):
            super().__setitem__(k.name, v)
        elif k in (fiat.name for fiat in Fiat):
            super().__setitem__(k, v)
        else:
            raise KeyError(f'Key {k} is invalid')
    def __getitem__(self, k):
        if isinstance(k, Fiat):
            return super().__getitem__(k.name)
        return super().__getitem__(k)

class Course(FiatDict):
    @classmethod
    def io_path(cls) -> str:
        return os.path.expanduser('~/.xmr-fiat.json')
    def __setitem__(self, k, v):
        val = Decimal(v)
        if val:
            super().__setitem__(k, val)
        else:
            raise ValueError(f'Value {val} is invalid')
    def load(self):
        with open(Course.io_path(), 'r') as f: 
            for key, val in json.load(f).items():
                self[key] = val
    def save(self):
        with open(Course.io_path(), 'w') as f:
            json.dump({key: float(val) for key, val in self.items()}, f)
    def load_mean_from(self, *apis):
        courses = FiatDict()
        for fiat in Fiat:
            courses[fiat] = []
        for api in apis:
            try:
                course = api()
                logger.info('API call {}(): {}', api.__name__, course)
                for fiat, val in course.items():
                    courses[fiat].append(val)
            except Exception as e:
                logger.error('API call {}() failed: {}', api.__name__, e)
        for fiat, val in courses.items():
            if val:
                self[fiat] = sum(val) / len(val)
            else:
                self[fiat] = Fiat.course[fiat]
                logger.error('all API calls for {} failed -> using prev value {}', fiat, self[fiat])

if __name__ == '__main__':
    Fiat.course = Course()
    Fiat.course.load()
    import apis
    Fiat.course.load_mean_from(apis.yahoo, apis.coinmarketcap)
    logger.info('course: {}', Fiat.course)
    logger.info('5 USD to XMR: {}', Fiat.USD.to_xmr(5))
    Fiat.course.save()