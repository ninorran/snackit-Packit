# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import fields, models

class NrSubmitDeliveryWizard(models.TransientModel):
    _name = 'nr.submit.delivery.wizard'
    _description = 'Submit Delivery Request Wizard'

    request_id = fields.Many2one('nr.delivery.request', required=True, readonly=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    consignee_id = fields.Many2one('res.partner', string='Consignee')
    def action_confirm(self):
        self.request_id.write({
            'supplier_id': self.supplier_id.id,
            'consignee_id': self.consignee_id.id,
            'state': 'approved',
        })
        self.request_id._send_whatsapp_notification('dr_approved')
        return {'type': 'ir.actions.act_window_close'}
