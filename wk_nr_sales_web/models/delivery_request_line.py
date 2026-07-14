# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

import math

from odoo import api, fields, models


class NrDeliveryRequestLine(models.Model):
    _name = 'nr.delivery.request.line'
    _description = 'NR Delivery Request Line'

    request_id = fields.Many2one('nr.delivery.request', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='request_id.currency_id')
    name = fields.Char(string='Tracking', required=True)
    description = fields.Text(string='Item Description')
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    declared_value = fields.Monetary(string='Declared Value', currency_field='currency_id')
    weight = fields.Float(string='Weight (lbs)', digits=(16, 4))
    duty_charge = fields.Monetary(string='Duty Charge', currency_field='currency_id')
    csc_charge = fields.Monetary(string='CSC Charge', currency_field='currency_id')
    vat_charge = fields.Monetary(string='VAT Charge', currency_field='currency_id')
    shipping_charge = fields.Monetary(string='Shipping Charge', currency_field='currency_id')
    insurance_charge = fields.Monetary(string='Insurance Charge', currency_field='currency_id')
    delivery_charge = fields.Monetary(string='Delivery Charge', currency_field='currency_id')
    notes = fields.Text(string='Additional Notes')

    @api.onchange('declared_value', 'weight')
    def _onchange_line_values(self):
        self._calc_charges(self.request_id.tariff_id)

    def _calc_charges(self, tariff):
        if tariff:
            duty = self.declared_value * (tariff.duty_charge / 100)
            csc = self.declared_value * (tariff.csc_charge / 100)
            taxable = self.declared_value + duty + csc
            vat = taxable * (tariff.vat_charge / 100)
            shipping = self.weight * tariff.shipping_rate if self.weight else 0.0
            bracket = tariff.insurance_bracket_value or 270.0
            charge = tariff.insurance_bracket_charge or 4.0
            insurance = math.ceil(self.declared_value / bracket) * charge if self.declared_value else 0.0
        else:
            duty = csc = vat = shipping = insurance = 0.0
        self.duty_charge = duty
        self.csc_charge = csc
        self.vat_charge = vat
        self.shipping_charge = shipping
        self.insurance_charge = insurance
