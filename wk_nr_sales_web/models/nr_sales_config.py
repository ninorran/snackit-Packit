# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class NrSalesConfig(models.Model):
    _name = 'nr.sales.config'
    _description = 'NR Sales Configuration'

    name = fields.Char(default='NR Sales Configuration')
    enable = fields.Boolean(string='Active', default=True)
    delivery_product_id = fields.Many2one(
        'product.product',
        string='Delivery Product',
        help='Product used when creating invoices for delivery requests.',
    )
    delivery_address_ids = fields.Many2many(
        'res.partner',
        'nr_sales_config_delivery_address_rel',
        'config_id', 'partner_id',
        string='Delivery Addresses',
        help='Available delivery addresses to assign to customers when granting portal access.',
    )
    whatsapp_event_ids = fields.One2many(
        'nr.whatsapp.event.config',
        'config_id',
        string='WhatsApp Events',
    )

    @api.constrains('enable')
    def _check_single_enabled(self):
        for rec in self:
            if rec.enable:
                others = self.search([('id', '!=', rec.id), ('enable', '=', True)])
                if others:
                    raise ValidationError(
                        _('Only one configuration can be enabled at a time. '
                          'Please disable "%s" before enabling this one.') % others[0].name
                    )

    def action_new_config(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nr.sales.config',
            'view_mode': 'form',
            'target': 'current',
        }

    @classmethod
    def _get_config(cls, env):
        config = env['nr.sales.config'].search([('enable', '=', True)], limit=1)
        return config or env['nr.sales.config'].create({})
