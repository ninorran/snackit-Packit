# -*- coding: utf-8 -*-

API_BASE_URL = 'https://app.sknpay.com/api/v1'
# Used when provider state == 'test'. Points to the local mock server.
TEST_API_BASE_URL = 'http://172.17.0.1:5001/api/v1'

SUPPORTED_CURRENCIES = ['USD', 'XCD']

# Mapping of SKNPay payment statuses to Odoo payment transaction states.
PAYMENT_STATUS_MAPPING = {
    'open':      'pending',
    'succeeded': 'done',
    'canceled':  'cancel',
    'expired':   'cancel',
    'failed':    'error',
}

DEFAULT_PAYMENT_METHOD_CODES = {
    # Primary payment methods.
    'card',
    # Brand payment methods.
    'visa',
    'mastercard',
}