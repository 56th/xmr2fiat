#!/usr/bin/env python3
import os, json, time
from enum import Enum, auto
from decimal import Decimal
from loguru import logger

class Fiat(Enum):
    USD = auto()
    EUR = auto()
    RUB = auto()
    def from_xmr(self, amt) -> Decimal:
        return Fiat.course[self] * Decimal(amt)
    def to_xmr(self, amt) -> Decimal:
        return Decimal(amt) / self.from_xmr(1)

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
        return os.path.expanduser('~/.xmr2fiat.json')
    def __setitem__(self, k, v):
        if v > 0:
            super().__setitem__(k, Decimal(v))
        else:
            raise ValueError(f'Value {v} is invalid')
    def load(self, default_value = 1) -> str:
        for fiat in Fiat:
            self[fiat] = default_value
        if os.path.isfile(Course.io_path()):
            with open(Course.io_path(), 'r') as f: 
                for key, val in json.load(f).items():
                    self[key] = val
            return time.ctime(os.path.getmtime(Course.io_path()))
        return time.ctime()
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
                logger.error('all API calls for {} failed -> using prev value {}', fiat, self[fiat])

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-u', '--update', action=argparse.BooleanOptionalAction, help='call APIs to update XMR course')
    parser.add_argument('-l', '--list', action=argparse.BooleanOptionalAction, help='list available fiat currencies')
    parser.add_argument('-f', '--fiat', type=lambda f: Fiat[f], default=Fiat.USD, choices=list(Fiat), help='currency to work with')
    parser.add_argument('-a', '--amount', type=float, default=0., help='amount to convert')
    args = parser.parse_args()
    if args.list:
        logger.info([fiat.name for fiat in Fiat])
    course = Course()        
    logger.info('last update: {}', course.load())
    if args.update:
        import apis
        course.load_mean_from(apis.yahoo, apis.coinmarketcap)
        logger.info('course: {}', course)
        course.save()
    if args.amount:
        Fiat.course = course
        logger.info('{} {} = {} XMR', args.amount, args.fiat.name, args.fiat.to_xmr(args.amount))
        logger.info('{} XMR = {} {}', args.amount, args.fiat.from_xmr(args.amount), args.fiat.name)