# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import fields, models


class NrDeliveryRequestLine(models.Model):
    _name = 'nr.delivery.request.line'
    _description = 'NR Delivery Request Line'

    request_id = fields.Many2one('nr.delivery.request', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='request_id.currency_id')
    name = fields.Char(string='Item Name', required=True)
    description = fields.Text(string='Item Description')
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    declared_value = fields.Monetary(string='Declared Value', currency_field='currency_id')
    weight = fields.Float(string='Weight (kg)')
    dimension_length = fields.Float(string='Length (cm)')
    dimension_width = fields.Float(string='Width (cm)')
    dimension_height = fields.Float(string='Height (cm)')
    notes = fields.Text(string='Additional Notes')
