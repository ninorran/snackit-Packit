# -*- coding: utf-8 -*-
import hashlib
import hmac
import re
import time

import requests
from werkzeug.exceptions import Forbidden

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_sknpay import const


_logger = get_payment_logger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('sknpay', 'SKNPay')],
        ondelete={'sknpay': 'set default'},
    )
    sknpay_api_key = fields.Char(
        string='SKNPay API Key',
        help='The test (sk_test_…) or live (sk_live_…) API key from SKNPay Settings → API keys.',
        required_if_provider='sknpay',
        copy=False,
        groups='base.group_system',
    )
    sknpay_webhook_secret = fields.Char(
        string='Webhook Secret',
        help='The whsec_… signing secret from SKNPay Settings → Webhooks.',
        copy=False,
        groups='base.group_system',
    )

    def _get_default_payment_method_codes(self):
        self.ensure_one()
        if self.code != 'sknpay':
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _compute_feature_support_fields(self):
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'sknpay').update({
            'support_refund': 'partial',
        })

    def _get_supported_currencies(self):
        supported = super()._get_supported_currencies()
        if self.code == 'sknpay':
            supported = supported.filtered(lambda c: c.name in const.SUPPORTED_CURRENCIES)
        return supported

    # === REQUEST HELPERS === #

    def _build_request_url(self, endpoint, **kwargs):
        if self.code != 'sknpay':
            return super()._build_request_url(endpoint, **kwargs)
        base = const.TEST_API_BASE_URL if self.state == 'test' else const.API_BASE_URL
        return f"{base}/{endpoint.strip('/')}"

    def _build_request_headers(self, *args, **kwargs):
        if self.code != 'sknpay':
            return super()._build_request_headers(*args, **kwargs)
        return {
            'Authorization': f'Bearer {self.sknpay_api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _parse_response_error(self, response):
        if self.code != 'sknpay':
            return super()._parse_response_error(response)
        return response.json().get('error', '')

    # === WEBHOOK SIGNATURE VERIFICATION === #

    def _sknpay_verify_signature(self, raw_body, header):
        """Verify the SknPay-Signature header using HMAC-SHA256.

        Format: t=<unix_timestamp>,v1=<hex_hmac>
        Signed payload: f'{timestamp}.{raw_body}'
        Replay window: 5 minutes.
        """
        self.ensure_one()
        m = re.match(r'^t=(\d+),v1=([0-9a-f]{64})$', header or '')
        if not m:
            _logger.warning("SKNPay: missing or malformed SknPay-Signature header")
            return False
        t, v1 = int(m.group(1)), m.group(2)
        if abs(int(time.time()) - t) > 300:
            _logger.warning("SKNPay: webhook signature timestamp outside 5-minute window")
            return False
        if not self.sknpay_webhook_secret:
            _logger.warning("SKNPay: webhook secret not configured")
            return False
        expected = hmac.new(
            self.sknpay_webhook_secret.encode(),
            f'{t}.{raw_body.decode()}'.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, v1)
