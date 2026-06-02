# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import urls

from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_sknpay import const
from odoo.addons.payment_sknpay.controllers.main import SKNPayController


_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return SKNPay-specific rendering values (redirect flow)."""
        if self.provider_code != 'sknpay':
            return super()._get_specific_rendering_values(processing_values)

        base_url = self.provider_id.get_base_url().replace('http://', 'https://', 1)
        return_url = urls.urljoin(base_url, f'{SKNPayController._return_url}?ref={self.reference}')
        webhook_url = urls.urljoin(base_url, SKNPayController._webhook_url)

        # Amount in minor currency units (cents).
        amount_minor = int(round(self.amount * (10 ** self.currency_id.decimal_places)))

        payload = {
            'amount': amount_minor,
            'currency': 'XCD',  # TODO: revert once XCD is configured in Odoo
            'description': self.reference,
            'success_url': return_url,
            'cancel_url': base_url,
            'metadata': {'reference': self.reference},
        }
        if self.partner_email:
            payload['customer_email'] = self.partner_email
        if self.partner_name:
            payload['customer_name'] = self.partner_name

        try:
            payment_data = self._send_api_request(
                'POST',
                'payments',
                json=payload,
                idempotency_key=self.reference,
            )
        except ValidationError as error:
            self._set_error(str(error))
            return {}

        self.provider_reference = payment_data.get('id')
        return {'api_url': payment_data['url']}

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        if provider_code != 'sknpay':
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get('ref')

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'sknpay':
            return super()._extract_amount_data(payment_data)
        amount_minor = payment_data.get('amount', 0)
        decimal_places = self.currency_id.decimal_places
        return {
            'amount': amount_minor / (10 ** decimal_places),
            'currency_code': payment_data.get('currency', ''),
        }

    def _apply_updates(self, payment_data):
        if self.provider_code != 'sknpay':
            return super()._apply_updates(payment_data)

        status = payment_data.get('status')
        if status == 'open':
            self._set_pending()
        elif status == 'succeeded':
            self._set_done()
        elif status in ('canceled', 'expired'):
            self._set_canceled(_("Payment %s.", status))
        elif status == 'failed':
            self._set_error(_("SKNPay payment failed."))
        else:
            _logger.info(
                "SKNPay: unhandled payment status '%s' for transaction %s.",
                status, self.reference,
            )

    def _send_refund_request(self):
        if self.provider_code != 'sknpay':
            return super()._send_refund_request()

        # self is the refund child transaction; source_transaction_id is the original payment.
        source_tx = self.source_transaction_id
        amount_minor = int(round(abs(self.amount) * (10 ** self.currency_id.decimal_places)))

        payload = {
            'payment_id': source_tx.provider_reference,
            'amount': amount_minor,
        }

        try:
            self._send_api_request('POST', 'refunds', json=payload)
        except ValidationError as error:
            self._set_error(str(error))
