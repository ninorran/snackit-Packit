# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models


class NrDeliveryRequestLine(models.Model):
    _name = 'nr.delivery.request.line'
    _description = 'NR Delivery Request Line'

    request_id = fields.Many2one('nr.delivery.request', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='request_id.currency_id')
    name = fields.Char(string='Item Name', required=True)
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
    insurance_charge = fields.Monetary(string='Insurance Charge', currency_field='currency_id')
    delivery_charge = fields.Monetary(string='Delivery Charge', currency_field='currency_id')
    notes = fields.Text(string='Additional Notes')

    @api.depends(
        'declared_value', 'weight',
        'request_id.tariff_id',
        'request_id.tariff_id.duty_charge',
        'request_id.tariff_id.csc_charge',
        'request_id.tariff_id.vat_charge',
        'request_id.tariff_id.shipping_rate',
    )
    def _compute_charges(self):
        for line in self:
            tariff = line.request_id.tariff_id
            if tariff:
                duty = line.declared_value * (tariff.duty_charge / 100)
                csc = line.declared_value * (tariff.csc_charge / 100)
                taxable = line.declared_value + duty + csc
                vat = taxable * (tariff.vat_charge / 100)
                shipping = line.weight * tariff.shipping_rate if line.weight else 0.0
            else:
                duty = csc = vat = shipping = 0.0
            line.duty_charge = duty
            line.csc_charge = csc
            line.vat_charge = vat
            line.shipping_charge = shipping
