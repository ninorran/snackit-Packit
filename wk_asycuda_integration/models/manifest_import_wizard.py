# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import _, fields, models
from odoo.exceptions import UserError


class ManifestImportWizard(models.TransientModel):
    _name = "wk.manifest.import.wizard"
    _description = "Import ASYCUDA Manifest XML"

    file_data = fields.Binary(string="Manifest XML File", required=True)
    file_name = fields.Char(string="Filename")

    def action_import(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        active_model = self.env.context.get("active_model", "stock.picking")
        if not active_id:
            raise UserError(_("No record found in context."))

        record = self.env[active_model].browse(active_id)
        if not record.exists():
            raise UserError(_("The selected record no longer exists."))

        record.action_import_manifest_xml_data(self.file_data)
        return {"type": "ir.actions.act_window_close"}
