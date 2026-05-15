# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import fields, models
from .nr_whatsapp_utils import send_nr_partner_whatsapp


class NrParcelReceivedWizard(models.TransientModel):
    _name = 'nr.parcel.received.wizard'
    _description = 'Set Parcel Received Date'

    request_id = fields.Many2one('nr.delivery.request', required=True, readonly=True)
    date_received = fields.Datetime(string='Date Received', default=fields.Datetime.now)

    def action_confirm(self):
        self.ensure_one()
        self.request_id.write({
            'state': 'parcel_received',
            'date_received': self.date_received,
        })
        self.request_id._send_whatsapp_notification('dr_parcel_received')
