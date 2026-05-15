# -*- coding: utf-8 -*-

from odoo import models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def action_open_preview(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.id}?download=false',
            'target': 'new',
        }
