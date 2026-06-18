# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import fields, models


class NrTariffConfig(models.Model):
    _name = 'nr.tariff.config'
    _description = 'NR Sales Tariff Configuration'

    name = fields.Char(required=True)
    duty_charge = fields.Float(string='Duty Charge (%)', digits=(16, 4))
    csc_charge = fields.Float(string='CSC Charge (%)', digits=(16, 4))
    vat_charge = fields.Float(string='VAT Charge (%)', digits=(16, 4))
    shipping_rate = fields.Float(string='Shipping Rate (XCD/lb)', digits=(16, 4))
