# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BatchContainer(models.Model):
    _name = "batch.container"
    _description = "Batch Transfer Container / AWB"

    batch_id = fields.Many2one("stock.picking.batch", string="Batch Transfer", required=True, ondelete="cascade")
    container_number = fields.Char(string="Container Number", required=True)
    package_count = fields.Integer(string="Package Count", default=0)
    weight = fields.Float(string="Weight", digits=(16, 3), default=0.0)
    volume = fields.Float(string="Volume", digits=(16, 3), default=0.0)
    type_of_container = fields.Char(string="Type of Container", default="20GP")
    empty_full = fields.Char(string="Empty/Full", default="LCL")
    marks1 = fields.Char(string="Marks 1")
    hs_code = fields.Char(string="HS Code")
    description = fields.Char(string="Description")
    customer_id = fields.Many2one("res.partner", string="Customer", domain=[("customer_rank", ">", 0)])
    customer_address = fields.Char(string="Customer Address", compute="_compute_customer_address", store=True)
    supplier_id = fields.Many2one("res.partner", string="Supplier", domain=[("supplier_rank", ">", 0)])
    supplier_address = fields.Char(string="Supplier Address", compute="_compute_supplier_address", store=True)

    @api.depends("customer_id", "customer_id.street", "customer_id.street2", "customer_id.city", "customer_id.zip", "customer_id.country_id")
    def _compute_customer_address(self):
        for rec in self:
            rec.customer_address = self._format_address(rec.customer_id)

    @api.depends("supplier_id", "supplier_id.street", "supplier_id.street2", "supplier_id.city", "supplier_id.zip", "supplier_id.country_id")
    def _compute_supplier_address(self):
        for rec in self:
            rec.supplier_address = self._format_address(rec.supplier_id)

    def _format_address(self, partner):
        if not partner:
            return ""
        parts = [partner.street, partner.street2, partner.city, partner.zip, partner.country_id.code]
        return ", ".join(p for p in parts if p)
