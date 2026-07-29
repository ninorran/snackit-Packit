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

    duty_charge = fields.Monetary(
        string='Duty Charge', currency_field='currency_id',
        compute='_compute_charges', store=True, readonly=False,
    )
    csc_charge = fields.Monetary(
        string='CSC Charge', currency_field='currency_id',
        compute='_compute_charges', store=True, readonly=False,
    )
    vat_charge = fields.Monetary(
        string='VAT Charge', currency_field='currency_id',
        compute='_compute_charges', store=True, readonly=False,
    )
    shipping_charge = fields.Monetary(
        string='Shipping Charge', currency_field='currency_id',
        compute='_compute_charges', store=True, readonly=False,
    )
    insurance_charge = fields.Monetary(
        string='Insurance Charge', currency_field='currency_id',
        compute='_compute_charges', store=True, readonly=False,
    )

    delivery_charge = fields.Monetary(string='Delivery Charge', currency_field='currency_id')
    notes = fields.Text(string='Additional Notes')

    @api.depends(
        'declared_value', 'weight',
        'request_id.tariff_id',
        'request_id.tariff_id.duty_charge',
        'request_id.tariff_id.csc_charge',
        'request_id.tariff_id.vat_charge',
        'request_id.tariff_id.shipping_rate',
        'request_id.tariff_id.insurance_bracket_value',
        'request_id.tariff_id.insurance_bracket_charge',
    )
    def _compute_charges(self):
        for rec in self:
            tariff = rec.request_id.tariff_id
            if tariff and rec.declared_value:
                duty = rec.declared_value * (tariff.duty_charge / 100)
                csc = rec.declared_value * (tariff.csc_charge / 100)
                taxable = rec.declared_value + duty + csc
                vat = taxable * (tariff.vat_charge / 100)
                shipping = rec.weight * tariff.shipping_rate if rec.weight else 0.0
                bracket = tariff.insurance_bracket_value or 270.0
                charge = tariff.insurance_bracket_charge or 4.0
                insurance = math.ceil(rec.declared_value / bracket) * charge
                rec.duty_charge = duty
                rec.csc_charge = csc
                rec.vat_charge = vat
                rec.shipping_charge = shipping
                rec.insurance_charge = insurance
            else:
                rec.duty_charge = 0.0
                rec.csc_charge = 0.0
                rec.vat_charge = 0.0
                rec.shipping_charge = 0.0
                rec.insurance_charge = 0.0

    def _calc_charges(self, *_):
        """Legacy helper — kept for parent onchange compatibility."""
        self._compute_charges()
