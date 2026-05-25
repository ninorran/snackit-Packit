# -*- coding: utf-8 -*-
import json
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment.logging import get_payment_logger


_logger = get_payment_logger(__name__)


class SKNPayController(http.Controller):
    _return_url = '/payment/sknpay/return'
    _webhook_url = '/payment/sknpay/webhook'

    @http.route(
        _return_url,
        type='http', auth='public', methods=['GET'], csrf=False, save_session=False,
    )
    def sknpay_return(self, **data):
        """Handle customer redirect back from SKNPay hosted checkout.

        SKNPay appends ?payment_id=<id> to success_url automatically. We also
        embed ?ref=<reference> ourselves so we can locate the transaction.
        """
        _logger.info("SKNPay: return from checkout with data:\n%s", pprint.pformat(data))

        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('sknpay', data)
        if tx_sudo:
            try:
                verified_data = tx_sudo._send_api_request(
                    'GET', f'payments/{tx_sudo.provider_reference}'
                )
            except ValidationError:
                _logger.exception("SKNPay: failed to verify payment on return")
            else:
                tx_sudo._process('sknpay', verified_data)

        return request.redirect('/payment/status')

    @http.route(
        _webhook_url,
        type='http', auth='public', methods=['POST'], csrf=False,
    )
    def sknpay_webhook(self):
        """Process signed webhook events from SKNPay."""
        raw = request.httprequest.get_data()
        sig = request.httprequest.headers.get('SknPay-Signature', '')

        _logger.info("SKNPay: webhook received, event-type: %s",
                     request.httprequest.headers.get('SknPay-Event-Type', ''))

        provider_sudo = request.env['payment.provider'].sudo().search(
            [('code', '=', 'sknpay'), ('state', '!=', 'disabled')], limit=1
        )
        if not provider_sudo or not provider_sudo._sknpay_verify_signature(raw, sig):
            _logger.warning("SKNPay: webhook signature verification failed")
            raise Forbidden()

        event = json.loads(raw)
        event_type = event.get('type', '')
        payment_obj = event.get('data', {}).get('object', {})
        reference = payment_obj.get('metadata', {}).get('reference', '')

        _logger.info("SKNPay: processing event '%s' for reference '%s'", event_type, reference)

        if not reference:
            _logger.warning("SKNPay: webhook missing reference in metadata, ignoring")
            return ''

        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'sknpay', {'ref': reference}
        )
        tx_sudo._process('sknpay', payment_obj)

        return ''
