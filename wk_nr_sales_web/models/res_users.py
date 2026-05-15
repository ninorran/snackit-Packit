# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models
from .nr_whatsapp_utils import send_nr_partner_whatsapp


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _update_last_login(self):
        super()._update_last_login()
        partner = self.partner_id
        if (
            partner.nr_sales_customer
            and partner.nr_sales_state == 'portal_access_sent'
        ):
            partner.sudo().write({'nr_sales_state': 'active'})
            send_nr_partner_whatsapp(self.env, 'account_active', partner)
