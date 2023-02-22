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
        return Fiat.course[self.name] * amt
    def to_xmr(self, amt: Decimal = 1) -> Decimal:
        return 1 / self.from_xmr(amt)

Course = Dict[str, Decimal]

def get_mean_course_from(*apis) -> Course:
    mean_course = {fiat.name: [] for fiat in Fiat}
    for api in apis:
        try:
            course = api()
        except Exception as e:
            logger.error('API call {}() failed: {}', api.__name__, e)
        logger.info('API call {}(): {}', api.__name__, course)
        for fiat, val in course.items():
            if val:
                mean_course[fiat].append(course[fiat])
            else:
                logger.error('API call {}() returned invalid value {} for {}', api.__name__, val, fiat)        
    for fiat in Fiat:
        if mean_course[fiat.name]:
            mean_course[fiat.name] = sum(mean_course[fiat.name]) / len(mean_course[fiat.name])
        else:
            mean_course[fiat.name] = Fiat.course[fiat.name]
            logger.error('all API calls for {} failed -> using prev value {}', fiat.name, mean_course[fiat.name])
    return mean_course

def import_course() -> Course:
    with open(os.path.expanduser('~/.xmr-fiat.json'), 'r') as f:
        try:
            return {Fiat[key].name: Decimal(val) for key, val in json.load(f).items()}
        except:
            logger.error('.xmr-fiat.json is inconsistent with Fiat enum')

Fiat.course = import_course()

def export_course(course: Course):
    with open(os.path.expanduser('~/.xmr-fiat.json'), 'w') as f:
        json.dump({key: float(val) for key, val in course.items()}, f)

if __name__ == '__main__':
    import apis
    Fiat.course = get_mean_course_from(apis.yahoo, apis.coinmarketcap)
    logger.info('course: {}', Fiat.course)
    logger.info('5 USD to XMR: {}', Fiat.USD.to_xmr(5))
    export_course(Fiat.course)