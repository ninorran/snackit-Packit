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


class NrDocumentCheckWizard(models.TransientModel):
    _name = 'nr.document.check.wizard'
    _description = 'Document Check Before Picking Creation'

    request_id = fields.Many2one('nr.delivery.request', required=True, readonly=True)

    has_purchase_invoice = fields.Boolean(compute='_compute_doc_status')
    has_supplier_invoice = fields.Boolean(compute='_compute_doc_status')
    has_shipping_documents = fields.Boolean(compute='_compute_doc_status')
    can_create_picking = fields.Boolean(compute='_compute_doc_status')

    @api.depends('request_id')
    def _compute_doc_status(self):
        for rec in self:
            rec.has_purchase_invoice = bool(rec.request_id.purchase_invoice_ids)
            rec.has_supplier_invoice = bool(rec.request_id.supplier_invoice_ids)
            rec.has_shipping_documents = bool(rec.request_id.shipping_document_ids)
            rec.can_create_picking = rec.has_purchase_invoice

    def action_send_wa_supplier_invoice(self):
        self.ensure_one()
        self.request_id._send_whatsapp_notification('request_supplier_invoice')

    def action_send_wa_purchase_invoice(self):
        self.ensure_one()
        self.request_id._send_whatsapp_notification('request_purchase_invoice')

    def action_send_wa_shipping_documents(self):
        self.ensure_one()
        self.request_id._send_whatsapp_notification('request_shipping_documents')

    def action_create_picking(self):
        self.ensure_one()
        if not self.can_create_picking:
            raise UserError(_('Purchase Invoice is required before creating a picking.'))
        return self.request_id.action_create_picking()
