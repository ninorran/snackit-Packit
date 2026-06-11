# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models, _


class NrSalesBillingWizard(models.TransientModel):
    _name = 'nr.nr_sales_billing_wizard'
    _description = 'NR Sales Billing Wizard'

    request_id = fields.Many2one('nr.delivery.request', required=True, readonly=True)
    tariff_id = fields.Many2one(
        'nr.tariff.config',
        string='Tariff Options',
        default=lambda self: self.env['nr.tariff.config'].search([], limit=1),
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    line_ids = fields.One2many('nr.nr_sales_billing_line', 'wizard_id', string='Lines')

    def _populate_lines(self):
        self.ensure_one()
        for item in self.request_id.line_ids:
            self.env['nr.nr_sales_billing_line'].create({
                'wizard_id': self.id,
                'item_name': item.name,
                'quantity': item.quantity,
                'declared_value': item.declared_value,
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
                if amount:
                    parts.append(f'  {label}: {amount:.2f}')

            invoice_line_vals.append((0, 0, {
                'name': '\n'.join(parts),
                'quantity': line.quantity,
                'price_unit': line.total,
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.request_id.partner_id.id,
            'invoice_origin': self.request_id.name,
            'invoice_line_ids': invoice_line_vals,
        })

        self.request_id.invoice_ids = [(4, invoice.id)]

        for billing_line in self.line_ids:
            matching = self.request_id.line_ids.filtered(
                lambda l: l.name == billing_line.item_name
            )[:1]
            if matching:
                matching.write({
                    'declared_value': billing_line.declared_value,
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

    item_name = fields.Char(string='Item Name', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    declared_value = fields.Monetary(string='Declared Value')

    duty_charge = fields.Monetary(
        string='Duty Charge',
        compute='_compute_charges', store=True, readonly=False,
    )
    csc_charge = fields.Monetary(
        string='CSC Charge',
        compute='_compute_charges', store=True, readonly=False,
    )
    vat_charge = fields.Monetary(
        string='VAT Charge',
        compute='_compute_charges', store=True, readonly=False,
    )

    shipping_charge = fields.Monetary(string='Shipping Charge')
    insurance_charge = fields.Monetary(string='Insurance Charge')
    delivery_charge = fields.Monetary(string='Delivery Charge')

    total = fields.Monetary(string='Total', compute='_compute_total', store=True)

    @api.depends(
        'declared_value',
        'wizard_id.tariff_id',
        'wizard_id.tariff_id.duty_charge',
        'wizard_id.tariff_id.csc_charge',
        'wizard_id.tariff_id.vat_charge',
    )
    def _compute_charges(self):
        for line in self:
            tariff = line.wizard_id.tariff_id
            if tariff:
                duty = line.declared_value * (tariff.duty_charge / 100)
                csc = line.declared_value * (tariff.csc_charge / 100)
                taxable = line.declared_value + duty + csc
                vat = taxable * (tariff.vat_charge / 100)
                line.duty_charge = duty
                line.csc_charge = csc
                line.vat_charge = vat
            else:
                line.duty_charge = 0.0
                line.csc_charge = 0.0
                line.vat_charge = 0.0

    @api.depends(
        'declared_value',
        'duty_charge', 'csc_charge', 'vat_charge',
        'shipping_charge', 'insurance_charge', 'delivery_charge',
    )
    def _compute_total(self):
        for line in self:
            line.total = (
                line.declared_value
                + line.duty_charge
                + line.csc_charge
                + line.vat_charge
                + line.shipping_charge
                + line.insurance_charge
                + line.delivery_charge
            )
