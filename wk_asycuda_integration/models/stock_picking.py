# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

import base64
from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "asycuda.manifest.mixin"]

    container_ids = fields.One2many("picking.container", "picking_id", string="Packages / AWBs")

    def action_generate_manifest_xml(self):
        self.ensure_one()
        self._check_manifest_requirements()
        xml_bytes = self._build_awmds_xml()
        filename = "%s.xml" % (self.name or "manifest")
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(xml_bytes),
            "mimetype": "application/xml",
            "res_model": "stock.picking",
            "res_id": self.id,
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }

    def action_open_manifest_import_wizard(self):
        self.ensure_one()
        action = self.env.ref("wk_asycuda_integration.action_wk_manifest_import_wizard").read()[0]
        action["context"] = dict(self.env.context, active_id=self.id, active_ids=self.ids, active_model=self._name)
        return action

    def action_load_packages_from_moves(self):
        self.ensure_one()
        move_lines = self.move_line_ids.filtered(lambda ml: ml.product_id)
        if not move_lines:
            move_lines = self.move_ids.filtered(lambda m: m.product_id).mapped("move_line_ids")
        if not move_lines:
            raise UserError(_("No product lines found on this picking to load."))

        commands = [(5, 0, 0)]
        for idx, ml in enumerate(move_lines, start=1):
            product = ml.product_id
            lot = ml.lot_id
            qty = ml.qty_done or ml.quantity or 1.0
            tracking_ref = (lot.name if lot else "") or ("%s-%03d" % (self.name.replace("/", ""), idx))
            weight = qty * (product.weight or 0.0)
            volume = qty * (product.volume or 0.0)
            hs_code = self._clip(getattr(product, "l10n_ec_hs_code", "") or getattr(product, "hs_code", "") or "", max_len=6, default="")
            commands.append((0, 0, {
                "container_number": self._clip(tracking_ref, max_len=17, default="PKG%014d" % idx),
                "package_count": 1,
                "weight": weight,
                "volume": volume,
                "description": self._clip(product.name, max_len=2000, default="GOODS"),
                "hs_code": hs_code,
                "marks1": self._clip(ml.lot_id.name or product.default_code or "", max_len=10, default=""),
                "type_of_container": "20GP",
                "empty_full": "LCL",
            }))
        self.write({"container_ids": commands})

    def action_import_manifest_xml_data(self, file_data):
        self.ensure_one()
        if not file_data:
            raise UserError(_("Please upload a manifest XML file first."))

        try:
            import base64 as _b64
            from lxml import etree
            xml_bytes = _b64.b64decode(file_data)
            root = etree.fromstring(xml_bytes)
        except Exception:
            raise UserError(_("Invalid XML file. Please upload a valid manifest XML."))

        if self._xml_local_name(root.tag) != "Awmds":
            raise UserError(_("Uploaded file is not a valid AWMDS manifest (root tag must be Awmds)."))

        vals = {}
        general_segment = self._xml_child(root, "General_segment")
        if general_segment is not None:
            general_id = self._xml_child(general_segment, "General_segment_id")
            if general_id is not None:
                self._set_if_present(vals, "customs_office_code", self._xml_child_text(general_id, "Customs_office_code"))
                self._set_if_present(vals, "voyage_number", self._xml_child_text(general_id, "Voyage_number"))

            totals_segment = self._xml_child(general_segment, "Totals_segment")
            if totals_segment is not None:
                vals["total_number_of_vehicles"] = self._to_int(
                    self._xml_child_text(totals_segment, "Total_number_of_vehicles"),
                    default=self.total_number_of_vehicles,
                )

            general_transport = self._xml_child(general_segment, "Transport_information")
            if general_transport is not None:
                general_carrier = self._xml_child(general_transport, "Carrier")
                if general_carrier is not None:
                    self._set_if_present(vals, "carrier_code", self._xml_child_text(general_carrier, "Carrier_code"))
                general_shipping_agent = self._xml_child(general_transport, "Shipping_Agent")
                if general_shipping_agent is not None:
                    self._set_if_present(vals, "shipping_agent_code", self._xml_child_text(general_shipping_agent, "Shipping_Agent_code"))
                self._set_if_present(vals, "mode_of_transport_code", self._xml_child_text(general_transport, "Mode_of_transport_code"))
                self._set_if_present(vals, "identity_of_transporter", self._xml_child_text(general_transport, "Identity_of_transporter"))
                self._set_if_present(vals, "nationality_of_transporter_code", self._xml_child_text(general_transport, "Nationality_of_transporter_code"))
                self._set_if_present(vals, "place_of_transporter", self._xml_child_text(general_transport, "Place_of_transporter"))
                self._set_if_present(vals, "registration_number_of_transport_code", self._xml_child_text(general_transport, "Registration_number_of_transport_code"))
                self._set_if_present(vals, "master_information", self._xml_child_text(general_transport, "Master_information"))

            general_load_unload = self._xml_child(general_segment, "Load_unload_place")
            if general_load_unload is not None:
                self._set_if_present(vals, "place_of_departure_code", self._xml_child_text(general_load_unload, "Place_of_departure_code"))
                self._set_if_present(vals, "place_of_destination_code", self._xml_child_text(general_load_unload, "Place_of_destination_code"))

        bol_segments = self._xml_children(root, "Bol_segment")
        container_commands = []
        first_bol = True
        for bol_segment in bol_segments:
            if first_bol:
                bol_id_el = self._xml_child(bol_segment, "Bol_id")
                if bol_id_el is not None:
                    self._set_if_present(vals, "bol_nature", self._xml_child_text(bol_id_el, "Bol_nature"))
                    self._set_if_present(vals, "bol_type_code", self._xml_child_text(bol_id_el, "Bol_type_code"))
                    self._set_if_present(vals, "fas_liner_cargo", self._xml_child_text(bol_id_el, "FAS_Liner_Cargo"))

                bol_load_unload = self._xml_child(bol_segment, "Load_unload_place")
                if bol_load_unload is not None:
                    if "place_of_departure_code" not in vals:
                        self._set_if_present(vals, "place_of_departure_code", self._xml_child_text(bol_load_unload, "Place_of_loading_code"))
                    if "place_of_destination_code" not in vals:
                        self._set_if_present(vals, "place_of_destination_code", self._xml_child_text(bol_load_unload, "Place_of_unloading_code"))

                goods_segment = self._xml_child(bol_segment, "Goods_segment")
                if goods_segment is not None:
                    self._set_if_present(vals, "package_type_code", self._xml_child_text(goods_segment, "Package_type_code"))
                    vals["num_of_vehicles_for_this_bol"] = self._to_int(
                        self._xml_child_text(goods_segment, "Num_of_vehicles_for_this_bol"),
                        default=self.num_of_vehicles_for_this_bol,
                    )
                    seals_segment = self._xml_child(goods_segment, "Seals_segment")
                    if seals_segment is not None:
                        vals["number_of_seals"] = self._to_int(self._xml_child_text(seals_segment, "Number_of_seals"), default=self.number_of_seals)
                        self._set_if_present(vals, "marks_of_seals", self._xml_child_text(seals_segment, "Marks_of_seals"))
                        self._set_if_present(vals, "sealing_party_code", self._xml_child_text(seals_segment, "Sealing_party_code"))

                value_segment = self._xml_child(bol_segment, "Value_segment")
                if value_segment is not None:
                    freight_segment = self._xml_child(value_segment, "Freight_segment")
                    if freight_segment is not None:
                        self._set_if_present(vals, "freight_pc_indicator", self._xml_child_text(freight_segment, "PC_indicator"))
                        vals["freight_value"] = self._to_float(self._xml_child_text(freight_segment, "Freight_value"), default=self.freight_value)
                        self._set_if_present(vals, "freight_currency", self._xml_child_text(freight_segment, "Freight_currency"))
                    transport_segment = self._xml_child(value_segment, "Transport_segment")
                    if transport_segment is not None:
                        vals["transport_value"] = self._to_float(self._xml_child_text(transport_segment, "Transport_value"), default=self.transport_value)
                        self._set_if_present(vals, "transport_currency", self._xml_child_text(transport_segment, "Transport_currency"))

                first_bol = False

            bol_id_el = self._xml_child(bol_segment, "Bol_id")
            bol_reference = self._xml_child_text(bol_id_el, "Bol_reference") if bol_id_el is not None else ""
            goods_segment = self._xml_child(bol_segment, "Goods_segment")
            pkg_count = 1
            gross_mass = 0.0
            description = ""
            volume = 0.0
            if goods_segment is not None:
                pkg_count = self._to_int(self._xml_child_text(goods_segment, "Number_of_packages"), default=1)
                gross_mass = self._to_float(self._xml_child_text(goods_segment, "Gross_mass"), default=0.0)
                description = self._xml_child_text(goods_segment, "Goods_description")
                volume = self._to_float(self._xml_child_text(goods_segment, "Volume_in_cubic_meters"), default=0.0)

            ctn_vals = {
                "container_number": self._clip(bol_reference, max_len=17, default="PKG0000000000000"),
                "package_count": pkg_count,
                "weight": gross_mass,
                "volume": volume,
                "type_of_container": "20GP",
                "empty_full": "LCL",
                "description": self._clip(description, max_len=2000, default=""),
            }
            if not container_commands:
                container_commands.append((5, 0, 0))
            container_commands.append((0, 0, ctn_vals))

        if vals:
            self.write(vals)
        if container_commands:
            self.write({"container_ids": container_commands})
        return True
