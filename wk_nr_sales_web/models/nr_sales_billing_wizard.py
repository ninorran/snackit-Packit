# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

import math

from odoo import api, fields, models, _


class NrSalesBillingWizard(models.TransientModel):
    _name = 'nr.nr_sales_billing_wizard'
    _description = 'NR Sales Billing Wizard'

    request_id = fields.Many2one('nr.delivery.request', required=True, readonly=True)
    tariff_id = fields.Many2one(
        'nr.tariff.config',
        string='Tariff Options',
        default=lambda self: self.env['nr.tariff.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        ),
    )
    company_id = fields.Many2one(related='request_id.company_id')
    currency_id = fields.Many2one(related='request_id.company_id.currency_id')
    line_ids = fields.One2many('nr.nr_sales_billing_line', 'wizard_id', string='Lines')

    def _populate_lines(self):
        self.ensure_one()
        for item in self.request_id.line_ids:
            self.env['nr.nr_sales_billing_line'].create({
                'wizard_id': self.id,
                'item_name': item.name,
                'product_description': item.description,
                'quantity': item.quantity,
                'declared_value': item.declared_value,
                'weight': item.weight,
                'duty_charge': item.duty_charge,
                'csc_charge': item.csc_charge,
                'vat_charge': item.vat_charge,
                'shipping_charge': item.shipping_charge,
                'insurance_charge': item.insurance_charge,
                'delivery_charge': item.delivery_charge,
            })

    def action_confirm(self):
        self.ensure_one()
        invoice_line_vals = []
        for line in self.line_ids:
            parts = [line.item_name]
            for label, amount in [
                ('Declared Value',   line.declared_value),
                ('Duty Charge',      line.duty_charge),
                ('CSC Charge',       line.csc_charge),
                ('VAT Charge',       line.vat_charge),
                ('Shipping Charge',  line.shipping_charge),
                ('Insurance Charge', line.insurance_charge),
                ('Delivery Charge',  line.delivery_charge),
            ]:
                parts.append(f'  {label}: {amount:.2f}')

            invoice_line_vals.append((0, 0, {
                'name': '\n'.join(parts),
                'product_description': line.product_description,
                'weight': line.weight,
                'quantity': line.quantity,
                'price_unit': line.total,
            }))

        company = self.request_id.company_id
        invoice = self.env['account.move'].with_company(company).create({
            'move_type': 'out_invoice',
            'nr_invoice_type': 'nr_sales_bill',
            'company_id': company.id,
            'partner_id': self.request_id.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.request_id.name,
            'invoice_line_ids': invoice_line_vals,
        })

        self.request_id.invoice_ids = [(4, invoice.id)]
        self.request_id.tariff_id = self.tariff_id

        for billing_line in self.line_ids:
            matching = self.request_id.line_ids.filtered(
                lambda l: l.name == billing_line.item_name
            )[:1]
            if matching:
                matching.write({
                    'weight': billing_line.weight,
                    'declared_value': billing_line.declared_value,
                    'duty_charge': billing_line.duty_charge,
                    'csc_charge': billing_line.csc_charge,
                    'vat_charge': billing_line.vat_charge,
                    'shipping_charge': billing_line.shipping_charge,
                    'insurance_charge': billing_line.insurance_charge,
                    'delivery_charge': billing_line.delivery_charge,
                })

        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }


class NrSalesBillingLine(models.TransientModel):
    _name = 'nr.nr_sales_billing_line'
    _description = 'NR Sales Billing Line'

    wizard_id = fields.Many2one('nr.nr_sales_billing_wizard', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='wizard_id.currency_id')

    item_name = fields.Char(string='Tracking #', required=True)
    product_description = fields.Text(string='Product Description')
    quantity = fields.Float(string='Quantity', default=1.0)
    declared_value = fields.Monetary(string='Declared Value')
    weight = fields.Float(string='Weight (lbs)', digits=(16, 4))

    duty_charge = fields.Monetary(string='Duty Charge')
    csc_charge = fields.Monetary(string='CSC Charge')
    vat_charge = fields.Monetary(string='VAT Charge')
    shipping_charge = fields.Monetary(string='Shipping Charge')
    insurance_charge = fields.Monetary(string='Insurance Charge')
    delivery_charge = fields.Monetary(string='Delivery Charge')

    total = fields.Monetary(string='Total', compute='_compute_total', store=True)

    @api.onchange('declared_value', 'weight', 'wizard_id')
    def _onchange_recalculate(self):
        tariff = self.wizard_id.tariff_id
        if tariff:
            duty = self.declared_value * (tariff.duty_charge / 100)
            csc = self.declared_value * (tariff.csc_charge / 100)
            taxable = self.declared_value + duty + csc
            vat = taxable * (tariff.vat_charge / 100)
            shipping = self.weight * tariff.shipping_rate if self.weight else 0.0
            bracket = tariff.insurance_bracket_value or 270.0
            charge = tariff.insurance_bracket_charge or 4.0
            insurance = math.ceil(self.declared_value / bracket) * charge if self.declared_value else 0.0
            self.duty_charge = duty
            self.csc_charge = csc
            self.vat_charge = vat
            self.shipping_charge = shipping
            self.insurance_charge = insurance

    @api.depends(
        'duty_charge', 'csc_charge', 'vat_charge',
        'shipping_charge', 'insurance_charge', 'delivery_charge',
    )
    def _compute_total(self):
        for line in self:
            line.total = (
                line.duty_charge
                + line.csc_charge
                + line.vat_charge
                + line.shipping_charge
                + line.insurance_charge
                + line.delivery_charge
            )
