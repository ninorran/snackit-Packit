# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models

NR_WHATSAPP_EVENTS = [
    ('registration',                'Customer Registration'),
    ('portal_invite',               'Portal Access Granted'),
    ('account_active',              'Account Activated'),
    ('dr_approved',                 'DR: Approved'),
    ('dr_awaiting_parcel',          'DR: Awaiting Parcel'),
    ('dr_parcel_received',          'DR: Parcel Received'),
    ('dr_in_transit',               'DR: In Transit'),
    ('dr_in_custom_clearance',      'DR: In Custom Clearance'),
    ('dr_passed_custom_clearance',  'DR: Passed Custom Clearance'),
    ('dr_failed_custom_clearance',  'DR: Failed Custom Clearance'),
    ('dr_out_for_delivery',         'DR: Out for Delivery'),
    ('dr_delivered',                'DR: Delivered'),
    ('dr_delivery_failed',          'DR: Delivery Failed'),
    ('dr_package_returned',         'DR: Package Returned'),
    ('dr_on_hold',                  'DR: On Hold'),
    ('dr_cancelled',                'DR: Cancelled'),
    ('request_supplier_invoice',    'Request: Supplier Invoice'),
    ('request_purchase_invoice',    'Request: Purchase Invoice'),
    ('request_shipping_documents',  'Request: Shipping Documents'),
]


class NrWhatsappEventConfig(models.Model):
    _name = 'nr.whatsapp.event.config'
    _description = 'NR Sales WhatsApp Event Configuration'
    _rec_name = 'event'

    config_id = fields.Many2one('nr.sales.config', required=True, ondelete='cascade')
    event = fields.Selection(NR_WHATSAPP_EVENTS, required=True, string='Event')
    wa_template_id = fields.Many2one(
        'whatsapp.template',
        string='WhatsApp Template',
        required=True
    )
    # domain=[('status', '=', 'approved')],
    enable = fields.Boolean(default=True)

    _sql_constraints = [
        ('event_config_unique', 'UNIQUE(config_id, event)',
        'Only one template can be configured per event.'),
    ]

    @api.model
    def _get_template_for_event(self, event_key):
        """Return the approved whatsapp.template for the given event, or None."""
        config = self.search([('event', '=', event_key), ('enable', '=', True)], limit=1)
        if config and config.wa_template_id and config.wa_template_id.status == 'approved':
            return config.wa_template_id
        return None
