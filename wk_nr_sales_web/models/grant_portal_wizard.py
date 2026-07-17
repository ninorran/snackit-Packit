# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class NrGrantPortalWizard(models.TransientModel):
    _name = 'nr.grant.portal.wizard'
    _description = 'Grant NR Sales Portal Access'

    partner_id = fields.Many2one('res.partner', required=True, readonly=True)
    delivery_address_id = fields.Many2one(
        'res.partner',
        string='Delivery Address',
        help='The delivery address that will be included in the portal invitation email.',
    )
    delivery_address_domain = fields.Many2many(
        'res.partner',
        compute='_compute_delivery_address_domain',
    )

    @api.depends('partner_id')
    def _compute_delivery_address_domain(self):
        config = self.env['nr.sales.config']._get_config(self.env)
        for rec in self:
            rec.delivery_address_domain = config.delivery_address_ids

    def action_grant_access(self):
        self.ensure_one()
        if not self.delivery_address_id:
            raise UserError(_('Please select a delivery address before granting access.'))

        partner = self.partner_id
        wizard = self.env['portal.wizard'].create({'partner_ids': [partner.id]})
        wizard_user = wizard.user_ids.filtered(lambda u: u.partner_id == partner)
        if not wizard_user or wizard_user.is_portal or wizard_user.is_internal:
            raise UserError(_('Portal access cannot be granted for this customer.'))

        wizard_user.with_context(
            delivery_address=self.delivery_address_id,
        ).action_grant_access()
