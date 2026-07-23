# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    nr_invoice_type = fields.Selection([
        ('nr_sales_bill', 'NR Sales Bill'),
        ('other', 'Other Purpose'),
    ], string='NR Invoice Type', index=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_description = fields.Text(string='Product Description')
    weight = fields.Float(string='Weight', digits=(16, 4))
