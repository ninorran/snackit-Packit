# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import fields, models, _


class NrCreateInvoiceWizard(models.TransientModel):
    _name = 'nr.create.invoice.wizard'
    _description = 'Create Invoice for Delivery Request'

    request_id = fields.Many2one('nr.delivery.request', required=True, readonly=True)
    invoice_type = fields.Selection([
        ('nr_sales_bill', 'For NR Sales Bill'),
        ('other', 'For Other Purposes'),
    ], string='Invoice Type', required=True, default='nr_sales_bill')

    company_id = fields.Many2one(related='request_id.company_id')
    currency_id = fields.Many2one(related='request_id.company_id.currency_id')
    amount = fields.Monetary(string='Amount')
    other_description = fields.Text(string='Description')

    def action_confirm(self):
        self.ensure_one()
        if self.invoice_type == 'other':
            company = self.request_id.company_id
            invoice = self.env['account.move'].with_company(company).create({
                'move_type': 'out_invoice',
                'nr_invoice_type': 'other',
                'company_id': company.id,
                'partner_id': self.request_id.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_origin': self.request_id.name,
                'invoice_line_ids': [(0, 0, {
                    'name': self.other_description or self.request_id.name,
                    'quantity': 1,
                    'price_unit': self.amount,
                })],
            })
            self.request_id.invoice_ids = [(4, invoice.id)]
            return {
                'name': _('Invoice'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
            }

        billing = self.env['nr.nr_sales_billing_wizard'].create({
            'request_id': self.request_id.id,
            'tariff_id': self.request_id.tariff_id.id or False,
        })
        billing._populate_lines()
        return {
            'name': _('NR Sales Bill'),
            'type': 'ir.actions.act_window',
            'res_model': 'nr.nr_sales_billing_wizard',
            'res_id': billing.id,
            'view_mode': 'form',
            'target': 'new',
        }
