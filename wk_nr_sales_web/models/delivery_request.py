# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class NrDeliveryRequest(models.Model):
    _name = 'nr.delivery.request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'NR Sales Delivery Request'
    _order = 'create_date desc'
    _allow_copy = False

    name = fields.Char(string='Reference', readonly=True, default='New', tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company, tracking=True,
    )
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    currency_id = fields.Many2one(related='company_id.currency_id', depends=['company_id'], store=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('awaiting_parcel', 'Awaiting Parcel'),
            ('parcel_received', 'Parcel Received'),
            ('in_transit', 'In Transit'),
            ('in_custom_clearance', 'In Custom Clearance'),
            ('passed_custom_clearance', 'Passed Custom Clearance'),
            ('failed_custom_clearance', 'Failed Custom Clearance'),
            ('out_for_delivery', 'Out for Delivery'),
            ('delivered', 'Delivered'),
            ('delivery_failed', 'Delivery Failed'),
            ('package_returned', 'Package Returned'),
            ('on_hold', 'On Hold'),
            ('cancelled', 'Cancelled'),
        ], string='Status', default='draft', tracking=True)
    state_before_hold = fields.Char(string='State Before Hold', copy=False)
    date_received = fields.Datetime(string='Date Received', tracking=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', tracking=True)
    invoice_available = fields.Boolean(string='Invoice Available', tracking=True)
    tariff_id = fields.Many2one(
        'nr.tariff.config',
        string='Tariff Options',
        default=lambda self: self.env['nr.tariff.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        ),
    )
    skb_loc = fields.Char(string='SKB-Loc')
    line_ids = fields.One2many('nr.delivery.request.line', 'request_id', string='Items')

    @api.onchange('tariff_id')
    def _onchange_tariff_id(self):
        for line in self.line_ids:
            line._calc_charges(self.tariff_id)

    picking_ids = fields.Many2many(
        'stock.picking',
        'nr_delivery_request_picking_rel',
        'request_id', 'picking_id',
        string='Pickings',
        copy=False,
    )
    picking_count = fields.Integer(compute='_compute_picking_count')
    active_picking_count = fields.Integer(compute='_compute_picking_count')
    picking_cancellable = fields.Boolean(compute='_compute_picking_cancellable')

    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids)
            rec.active_picking_count = len(rec.picking_ids.filtered(lambda p: p.state != 'cancel'))

    def _compute_picking_cancellable(self):
        for rec in self:
            rec.picking_cancellable = not rec.picking_ids or all(
                p.state != 'done' for p in rec.picking_ids
            )

    invoice_ids = fields.Many2many(
        'account.move',
        'nr_delivery_request_invoice_rel',
        'request_id', 'invoice_id',
        string='Invoices',
        copy=False,
    )
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    payment_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partial Paid'),
        ('paid', 'Paid'),
    ], string='Payment Status', compute='_compute_payment_status', store=True)

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends('invoice_ids', 'invoice_ids.payment_state', 'invoice_ids.state',
                 'invoice_ids.move_type', 'invoice_ids.nr_invoice_type')
    def _compute_payment_status(self):
        for rec in self:
            invoices = rec.invoice_ids.filtered(
                lambda m: m.state == 'posted'
                and m.move_type == 'out_invoice'
                and m.nr_invoice_type == 'nr_sales_bill'
            )
            if not invoices:
                rec.payment_status = False
            elif all(m.payment_state in ('paid', 'in_payment', 'reversed') for m in invoices):
                rec.payment_status = 'paid'
            elif any(m.payment_state == 'partial' for m in invoices):
                rec.payment_status = 'partial'
            else:
                rec.payment_status = 'not_paid'

    supplier_invoice_ids = fields.Many2many(
        'ir.attachment',
        'nr_delivery_supplier_att_rel',
        'request_id', 'attachment_id',
        string='Supplier Invoice',
    )
    shipping_document_ids = fields.Many2many(
        'ir.attachment',
        'nr_delivery_shipping_att_rel',
        'request_id', 'attachment_id',
        string='Shipping Documents',
    )
    document_count = fields.Integer(compute='_compute_document_count')

    def _compute_document_count(self):
        for rec in self:
            rec.document_count = (
                len(rec.supplier_invoice_ids)
                + len(rec.shipping_document_ids)
            )

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list',
            'domain': [('id', 'in', (
                self.supplier_invoice_ids
                + self.shipping_document_ids
            ).ids)],
        }

    def action_open_document_check(self):
        self.ensure_one()
        wizard = self.env['nr.document.check.wizard'].create({'request_id': self.id})
        return {
            'name': _('Document Check'),
            'type': 'ir.actions.act_window',
            'res_model': 'nr.document.check.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_picking(self):
        self.ensure_one()
        config = self.env['nr.sales.config']._get_config(self.env)
        product = config.delivery_product_id

        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.company_id.id)], limit=1
        )
        picking_type = warehouse.out_type_id

        lines = self.line_ids
        if lines:
            move_description = _('Delivery Request: %s\n\nItems:\n') % self.name
            move_description += '\n'.join(
                '- %s (Qty: %g)%s' % (
                    line.name,
                    line.quantity,
                    ': ' + line.description if line.description else '',
                )
                for line in lines
            )
        else:
            move_description = _('Delivery Request: %s') % self.name

        if not product:
            raise UserError(_('Please set a Delivery Product in NR Sales Configuration before creating a picking.'))

        move_vals = {
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 1,
            'description_picking': move_description,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
        }

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'move_ids': [(0, 0, move_vals)],
        })
        self.picking_ids = [(4, picking.id)]
        return {
            'name': _('Picking'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
        }

    def action_view_pickings(self):
        self.ensure_one()
        if self.picking_count == 1:
            return {
                'name': _('Picking'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'res_id': self.picking_ids.id,
                'view_mode': 'form',
            }
        return {
            'name': _('Pickings'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
        }

    def action_create_invoice(self):
        self.ensure_one()
        wizard = self.env['nr.create.invoice.wizard'].create({'request_id': self.id})
        return {
            'name': _('Create Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'nr.create.invoice.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_invoices(self):
        self.ensure_one()
        if self.invoice_count == 1:
            return {
                'name': _('Invoice'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': self.invoice_ids.id,
                'view_mode': 'form',
            }
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
        }

    def _compute_access_url(self):
        for rec in self:
            rec.access_url = f'/my/delivery-requests/{rec.id}'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                company_id = vals.get('company_id') or self.env.company.id
                vals['name'] = (
                    self.env['ir.sequence'].with_company(company_id).sudo()
                    .next_by_code('nr.delivery.request') or 'New'
                )
        return super().create(vals_list)

    def action_submit(self):
        self.ensure_one()
        wizard = self.env['nr.submit.delivery.wizard'].create({
            'request_id': self.id,
            'supplier_id': self.supplier_id.id,
        })
        return {
            'name': _('Approve Delivery Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'nr.submit.delivery.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _send_whatsapp_notification(self, event_key):
        """Send a WhatsApp notification for a DR-level event. Silently skips if not configured."""
        template = self.env['nr.whatsapp.event.config']._get_template_for_event(event_key)
        if not template:
            return
        records = self.filtered(lambda r: r.partner_id.mobile or r.partner_id.phone)
        if not records:
            return
        try:
            self.env['whatsapp.composer'].sudo().create({
                'res_model': self._name,
                'res_ids': records.ids,
                'wa_template_id': template.id,
                'batch_mode': len(records) > 1,
            })._send_whatsapp_template(force_send_by_cron=True)
        except Exception:
            pass

    def action_await_parcel(self):
        self.write({'state': 'awaiting_parcel'})
        self._send_whatsapp_notification('dr_awaiting_parcel')

    def action_parcel_received(self):
        self.ensure_one()
        wizard = self.env['nr.parcel.received.wizard'].create({
            'request_id': self.id,
            'date_received': fields.Datetime.now(),
        })
        return {
            'name': _('Parcel Received'),
            'type': 'ir.actions.act_window',
            'res_model': 'nr.parcel.received.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_in_transit(self):
        self.write({'state': 'in_transit'})
        self._send_whatsapp_notification('dr_in_transit')

    def action_in_custom_clearance(self):
        self.write({'state': 'in_custom_clearance'})
        self._send_whatsapp_notification('dr_in_custom_clearance')

    def action_passed_custom_clearance(self):
        self.write({'state': 'passed_custom_clearance'})
        self._send_whatsapp_notification('dr_passed_custom_clearance')

    def action_failed_custom_clearance(self):
        self.write({'state': 'failed_custom_clearance'})
        self._send_whatsapp_notification('dr_failed_custom_clearance')

    def action_out_for_delivery(self):
        self.write({'state': 'out_for_delivery'})
        self._send_whatsapp_notification('dr_out_for_delivery')

    def action_delivered(self):
        self.write({'state': 'delivered'})
        self._send_whatsapp_notification('dr_delivered')

    def action_delivery_failed(self):
        self.write({'state': 'delivery_failed'})
        self._send_whatsapp_notification('dr_delivery_failed')

    def action_package_returned(self):
        self.write({'state': 'package_returned'})
        self._send_whatsapp_notification('dr_package_returned')

    def action_hold(self):
        for rec in self:
            rec.write({'state_before_hold': rec.state, 'state': 'on_hold'})
        self._send_whatsapp_notification('dr_on_hold')

    def action_resume(self):
        for rec in self:
            rec.write({'state': rec.state_before_hold or 'approved', 'state_before_hold': False})

    def action_cancel(self):
        for rec in self:
            for picking in rec.picking_ids:
                if picking.state not in ('done', 'cancel'):
                    picking.action_cancel()
            rec.state = 'cancelled'
        self._send_whatsapp_notification('dr_cancelled')

    def action_reset_draft(self):
        self.write({'state': 'draft'})
