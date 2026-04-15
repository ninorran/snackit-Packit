# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################
from odoo import fields, models


class PickingContainer(models.Model):
    _name = "picking.container"
    _description = "Picking Container"

    picking_id = fields.Many2one("stock.picking", string="Picking", required=True, ondelete="cascade")
    container_number = fields.Char(string="Container Number", required=True)
    package_count = fields.Integer(string="Package Count", default=0)
    weight = fields.Float(string="Weight", digits=(16, 3), default=0.0)
    volume = fields.Float(string="Volume", digits=(16, 3), default=0.0)
    type_of_container = fields.Char(string="Type of Container", default="20GP")
    empty_full = fields.Char(string="Empty/Full", default="LCL")
    marks1 = fields.Char(string="Marks 1")
    hs_code = fields.Char(string="HS Code")
    description = fields.Char(string="Description")
