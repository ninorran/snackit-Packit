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
    shipping_charge = fields.Monetary(
        string='Shipping Charge', currency_field='currency_id',
        compute='_compute_shipping_charge', store=True, readonly=False,
    )
    insurance_charge = fields.Monetary(string='Insurance Charge', currency_field='currency_id')
    delivery_charge = fields.Monetary(string='Delivery Charge', currency_field='currency_id')
    notes = fields.Text(string='Additional Notes')

    @api.depends('weight')
    def _compute_shipping_charge(self):
        tariff = self.env['nr.tariff.config'].search([], limit=1)
        for line in self:
            if tariff and line.weight:
                line.shipping_charge = line.weight * tariff.shipping_rate
            else:
                line.shipping_charge = 0.0
