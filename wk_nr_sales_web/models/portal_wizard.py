# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from .nr_whatsapp_utils import send_nr_partner_whatsapp


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    def action_grant_access(self):
        self.ensure_one()
        if self.partner_id.nr_sales_customer:
            vals = {'nr_sales_state': 'portal_access_sent'}
            if not self.partner_id.nr_sales_uid:
                vals['nr_sales_uid'] = self.env['ir.sequence'].sudo().next_by_code('nr.sales.customer.uid')
            self.partner_id.sudo().write(vals)
        return super().action_grant_access()

    def action_revoke_access(self):
        self.ensure_one()
        if self.partner_id.nr_sales_customer:
            self.partner_id.sudo().write({'nr_sales_state': 'revoked'})
        return super().action_revoke_access()

    def _send_email(self):
        self.ensure_one()
        if self.partner_id.nr_sales_customer:
            template = self.env.ref('wk_nr_sales_web.nr_sales_portal_invite_email')
            if not template:
                raise UserError(_('The NR Sales portal invite email template was not found.'))
            lang = self.user_id.sudo().lang
            partner = self.user_id.sudo().partner_id
            partner.signup_prepare()
            delivery_address = self.env.context.get('delivery_address')
            template.with_context(
                dbname=self.env.cr.dbname,
                lang=lang,
                welcome_message=self.wizard_id.welcome_message,
                medium='portalinvite',
                nr_sales_uid=self.partner_id.nr_sales_uid,
                delivery_address=delivery_address,
            ).send_mail(self.user_id.id, force_send=True)
            send_nr_partner_whatsapp(self.env, 'portal_invite', self.partner_id)
            return True
        return super()._send_email()
