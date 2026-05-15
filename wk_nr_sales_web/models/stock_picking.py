# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        result = super()._action_done()
        DRModel = self.env['nr.delivery.request']
        for picking in self:
            dr = DRModel.search([
                ('picking_ids', 'in', picking.id),
                ('state', '=', 'in_transit'),
            ])
            if dr:
                dr.write({'state': 'in_custom_clearance'})
        return result

    def action_cancel(self):
        result = super().action_cancel()
        DRModel = self.env['nr.delivery.request']
        for picking in self:
            dr = DRModel.search([
                ('picking_ids', 'in', picking.id),
                ('state', '=', 'in_transit'),
            ])
            if dr:
                dr.write({'state': 'parcel_received'})
        return result
