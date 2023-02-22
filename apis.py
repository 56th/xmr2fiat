import os, json
import yfinance as yf
from requests import Request, Session
from decimal import Decimal
from loguru import logger
from core import Fiat, Course

def yahoo() -> Course:
    data = yf.download(['XMR-' + fiat.name for fiat in Fiat], period='1d', progress=False).to_dict()
    course = Course()
    for fiat in Fiat:
        try:
            course[fiat] = list(data[('Close', 'XMR-' + fiat.name)].values())[0]
        except Exception as e:
            logger.error(e)    
    return course

def coinmarketcap() -> Course:
    session = Session()
    session.headers.update({
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': os.getenv('API_KEY_CMC')
    })
    course = Course()
    for fiat in Fiat:
        try:
            response = session.get('https://pro-api.coinmarketcap.com/v2/tools/price-conversion', params={
                'symbol': 'XMR',
                'amount': 1,
                'convert': fiat.name
            })
            data = json.loads(response.text)
            if data['status']['error_code']:
                raise ValueError(data['status']['error_message'])
            course[fiat] = data['data'][0]['quote'][fiat.name]['price']
        except Exception as e:
            logger.error(e)
    return course

def coinlayer() -> Course:
    """https://coinlayer.com/"""
    pass

def coinbase() -> Course:
    """https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getconversion"""
    pass