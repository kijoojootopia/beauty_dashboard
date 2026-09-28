from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from platform_core.integrations.http_client import IntegrationError, cached, request_json, setting


URL = 'https://v6.exchangerate-api.com/v6/latest/KRW'


def fetch():
    key = setting('EXCHANGE_API_KEY')
    if not key:
        return {'state': 'data_pending', 'message': 'ExchangeRate-API 인증키를 설정해 주세요.', 'data': {}}

    def load():
        response = request_json(URL, headers={'Authorization': f'Bearer {key}'})
        if not isinstance(response, dict):
            raise IntegrationError('환율 API 응답 형식을 확인할 수 없습니다.')
        if response.get('result') != 'success':
            messages = {
                'invalid-key': 'ExchangeRate-API 인증키를 확인해 주세요.',
                'inactive-account': 'ExchangeRate-API 계정의 이메일 인증을 확인해 주세요.',
                'quota-reached': 'ExchangeRate-API 호출 한도를 초과했습니다.',
            }
            raise IntegrationError(messages.get(response.get('error-type'), '환율 API 오류를 확인해 주세요.'))
        values = response.get('conversion_rates')
        if response.get('base_code') != 'KRW' or not isinstance(values, dict) or values.get('KRW') != 1:
            raise IntegrationError('환율 API 응답의 기준 통화를 확인해 주세요.')
        try:
            as_of = datetime.fromtimestamp(response['time_last_update_unix'], timezone.utc).date().isoformat()
        except (KeyError, TypeError, ValueError, OverflowError):
            raise IntegrationError('환율 API 응답의 기준일을 확인해 주세요.') from None
        rates = []
        for currency, value in values.items():
            try:
                rate = Decimal(str(value))
            except InvalidOperation:
                continue
            if len(currency) == 3 and currency.isalpha() and rate.is_finite() and rate > 0:
                rates.append({'currency': currency, 'unit': 1, 'krw_rate': str(1 / rate)})
        if not rates:
            raise IntegrationError('환율 API 응답에 유효한 환율이 없습니다.')
        return {'state': 'ready', 'message': '', 'data': {
            'as_of': as_of, 'source': 'ExchangeRate-API',
            'source_url': 'https://www.exchangerate-api.com/', 'rates': rates,
        }}

    return cached('exchange_rate_api', [key], load, ttl=3600)
