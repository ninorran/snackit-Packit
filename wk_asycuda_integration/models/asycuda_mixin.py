# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from datetime import date, datetime
from lxml import etree
from odoo import _, fields, models
from odoo.exceptions import UserError


class AsycudaManifestMixin(models.AbstractModel):
    _name = "asycuda.manifest.mixin"
    _description = "ASYCUDA Manifest Helpers"

    # ── Shared ASYCUDA fields ────────────────────────────────────────────────
    customs_office_code = fields.Char(string="Customs Office Code", help="5-character ASYCUDA reference code.")
    place_of_departure_code = fields.Char(string="Place of Departure Code", help="5-character ASYCUDA reference code.")
    place_of_destination_code = fields.Char(string="Place of Destination Code", help="5-character ASYCUDA reference code.")
    shipping_agent_code = fields.Char(
        string="Shipping Agent Code",
        help="Authorized Shipping Agent Code from ASYCUDA reference/master data (max 17 chars).",
    )
    carrier_code = fields.Char(string="Carrier Code", default="M6")
    mode_of_transport_code = fields.Char(string="Mode of Transport Code", default="4")
    voyage_number = fields.Char(string="Voyage Number")
    identity_of_transporter = fields.Char(string="Identity of Transporter")
    nationality_of_transporter_code = fields.Char(string="Nationality of Transporter Code", default="US")
    place_of_transporter = fields.Char(string="Place of Transporter")
    registration_number_of_transport_code = fields.Char(string="Registration Number of Transport")
    master_information = fields.Char(string="Master Information")
    bol_nature = fields.Selection(
        [("22", "22"), ("23", "23"), ("24", "24"), ("28", "28")],
        string="BOL Nature",
        default="23",
    )
    bol_type_code = fields.Char(string="BOL Type Code", default="AWB")
    fas_liner_cargo = fields.Selection([("F", "F"), ("L", "L")], string="FAS/Liner Cargo", default="F")
    package_type_code = fields.Char(string="Package Type Code", default="CT")
    number_of_seals = fields.Integer(string="Number of Seals", default=1)
    marks_of_seals = fields.Char(string="Marks of Seals", default="SALVAE")
    sealing_party_code = fields.Char(string="Sealing Party Code", default="SH")
    freight_pc_indicator = fields.Char(string="Freight PC Indicator", default="P")
    freight_value = fields.Float(string="Freight Value", default=0.0)
    freight_currency = fields.Char(string="Freight Currency", default="XCD")
    transport_value = fields.Float(string="Transport Value", default=0.0)
    transport_currency = fields.Char(string="Transport Currency", default="XCD")
    total_number_of_vehicles = fields.Integer(string="Total Number of Vehicles", default=0)
    num_of_vehicles_for_this_bol = fields.Integer(string="Vehicles for this BOL", default=0)

    # ── XML helpers ──────────────────────────────────────────────────────────

    def _xml_text(self, parent, tag, value):
        node = etree.SubElement(parent, tag)
        if value is None:
            return node
        value_str = str(value)
        if value_str:
            node.text = value_str
        return node

    def _aw_number(self, value):
        if value in (None, False):
            return "0"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return ("%.3f" % value).rstrip("0").rstrip(".")
        return str(value)

    def _aw_date(self, value):
        if not value:
            return fields.Date.to_string(fields.Date.context_today(self))
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        try:
            dt_value = fields.Datetime.to_datetime(value)
            if dt_value:
                return dt_value.date().isoformat()
        except Exception:
            pass
        try:
            d_value = fields.Date.to_date(value)
            if d_value:
                return d_value.isoformat()
        except Exception:
            pass
        return fields.Date.to_string(fields.Date.context_today(self))

    def _aw_time(self, value):
        if not value:
            return ""
        dt = value if isinstance(value, datetime) else None
        if dt is None:
            try:
                dt = fields.Datetime.to_datetime(value)
            except Exception:
                pass
        return dt.strftime("%H:%M:%S") if dt else ""

    def _value_or_default(self, value, default=""):
        if value in (None, False, ""):
            return default
        return value

    def _set_if_present(self, vals, key, value):
        if value not in (None, ""):
            vals[key] = value

    def _xml_local_name(self, tag):
        return tag.split("}", 1)[-1] if tag and "}" in tag else (tag or "")

    def _xml_child(self, node, name):
        if node is None:
            return None
        for child in node:
            if self._xml_local_name(child.tag) == name:
                return child
        return None

    def _xml_children(self, node, name):
        if node is None:
            return []
        return [child for child in node if self._xml_local_name(child.tag) == name]

    def _xml_child_text(self, node, name, default=""):
        child = self._xml_child(node, name)
        if child is None:
            return default
        return (child.text or "").strip()

    def _to_int(self, value, default=0):
        try:
            if value in (None, ""):
                return default
            return int(float(value))
        except Exception:
            return default

    def _to_float(self, value, default=0.0):
        try:
            if value in (None, ""):
                return default
            return float(value)
        except Exception:
            return default

    def _validate_max_len(self, value, field_name, max_len, required=False):
        text = ""
        if value not in (None, False):
            text = str(value).strip()
        if required and not text:
            raise UserError(_("%s is required.") % field_name)
        if text and len(text) > max_len:
            raise UserError(_("%s must be at most %s characters.") % (field_name, max_len))
        return text

    def _clip(self, value, max_len=None, default="", upper=False):
        text = ""
        if value not in (None, False):
            text = str(value).strip()
        if not text:
            text = default
        if upper:
            text = text.upper()
        if max_len and len(text) > max_len:
            text = text[:max_len]
        return text

    def _validate_reference_code(self, value, field_name):
        code = self._clip(value, max_len=5, default="", upper=True)
        if len(code) != 5:
            raise UserError(_("%s must be exactly 5 characters.") % field_name)
        return code

    def _partner_address(self, partner):
        if not partner:
            return ""
        parts = [partner.street, partner.street2, partner.city, partner.zip, partner.country_id.code]
        return ", ".join(part for part in parts if part)

    # ── Shared manifest requirements check (uses self.container_ids) ─────────

    def _check_manifest_requirements(self):
        self.ensure_one()
        if not self.container_ids:
            raise UserError(_("At least one package/AWB is required. Use 'Load Packages from Moves' or add them manually."))
        self._validate_reference_code(self.customs_office_code, _("Customs Office Code"))
        self._validate_reference_code(self.place_of_departure_code, _("Place of Departure Code"))
        self._validate_reference_code(self.place_of_destination_code, _("Place of Destination Code"))
        if not self.shipping_agent_code or not self.shipping_agent_code.strip():
            raise UserError(_("Shipping Agent Code is required before generating ASYCUDA manifest XML."))
        self._validate_max_len(self.shipping_agent_code, _("Shipping Agent Code"), 17, required=True)
        self._validate_max_len(self.carrier_code, _("Carrier Code"), 17)
        self._validate_max_len(self.mode_of_transport_code, _("Mode of Transport Code"), 3)
        self._validate_max_len(self.voyage_number, _("Voyage Number"), 17)
        self._validate_max_len(self.identity_of_transporter, _("Identity of Transporter"), 27)
        self._validate_max_len(self.nationality_of_transporter_code, _("Nationality of Transporter Code"), 3)
        self._validate_max_len(self.place_of_transporter, _("Place of Transporter"), 35)
        self._validate_max_len(self.registration_number_of_transport_code, _("Registration Number of Transport"), 35)
        self._validate_max_len(self.bol_type_code, _("BOL Type Code"), 3)
        self._validate_max_len(self.package_type_code, _("Package Type Code"), 17)
        self._validate_max_len(self.sealing_party_code, _("Sealing Party Code"), 3)
        self._validate_max_len(self.marks_of_seals, _("Marks of Seals"), 20)
        self._validate_max_len(self.freight_pc_indicator, _("Freight PC Indicator"), 3)
        self._validate_max_len(self.freight_currency, _("Freight Currency"), 3)
        self._validate_max_len(self.transport_currency, _("Transport Currency"), 3)

        if self.number_of_seals < 0:
            raise UserError(_("Number of Seals cannot be negative."))
        if self.total_number_of_vehicles < 0:
            raise UserError(_("Total Number of Vehicles cannot be negative."))
        if self.num_of_vehicles_for_this_bol < 0:
            raise UserError(_("Vehicles for this BOL cannot be negative."))

        for container in self.container_ids:
            if not container.customer_id:
                raise UserError(_("Customer is required on all packages/AWBs before generating the manifest XML."))
            if not container.supplier_id:
                raise UserError(_("Supplier is required on all packages/AWBs before generating the manifest XML."))
            self._validate_max_len(container.container_number, _("Package/AWB Number"), 17, required=True)
            self._validate_max_len(container.type_of_container, _("Type of Container"), 4)
            self._validate_max_len(container.empty_full, _("Empty/Full"), 3)
            self._validate_max_len(container.marks1, _("Marks 1"), 10)
            if (container.package_count or 0) < 0:
                raise UserError(_("Package Count cannot be negative."))
            if (container.weight or 0.0) < 0:
                raise UserError(_("Package Weight cannot be negative."))
            if (container.volume or 0.0) < 0:
                raise UserError(_("Package Volume cannot be negative."))

    # ── Shared XML builder (uses self.container_ids, self.name, self.create_date) ─

    def _build_awmds_xml(self):
        self.ensure_one()

        packages = self.container_ids
        company = self.company_id
        company_partner = company.partner_id

        total_bols = len(packages)
        total_packages = sum(packages.mapped("package_count"))
        total_gross_mass = sum(packages.mapped("weight"))

        carrier_code = self._clip(self.carrier_code or company_partner.ref, max_len=17, default="M6")
        shipping_agent_code = self._clip(self.shipping_agent_code, max_len=17, default="")
        mode_of_transport_code = self._clip(self.mode_of_transport_code, max_len=3, default="4")
        voyage_number = self._clip(self.voyage_number or getattr(self, "origin", None) or self.name, max_len=17, default="TRADER3")
        identity_of_transporter = self._clip(
            self.identity_of_transporter or company.name, max_len=27, default="AMERICAN AIRLINES",
        )
        nationality_of_transporter_code = self._clip(
            self.nationality_of_transporter_code or company_partner.country_id.code,
            max_len=3, default="US", upper=True,
        )
        place_of_transporter = self._clip(
            self.place_of_transporter or company_partner.city, max_len=35, default="MIAMI",
        )
        registration_number_of_transport_code = self._clip(
            self.registration_number_of_transport_code or self.name, max_len=35, default="",
        )
        master_information = self._clip(
            self.master_information or getattr(self, "user_id", self.env.user).name,
            max_len=70, default="",
        )
        bol_type_code = self._clip(self.bol_type_code, max_len=3, default="AWB")
        package_type_code = self._clip(self.package_type_code, max_len=17, default="CT")
        seals_count = max(self.number_of_seals or 0, 0)
        marks_of_seals = self._clip(self.marks_of_seals, max_len=20, default="SALVAE")
        sealing_party_code = self._clip(self.sealing_party_code, max_len=3, default="SH")
        freight_pc_indicator = self._clip(self.freight_pc_indicator, max_len=3, default="P")
        freight_currency = self._clip(self.freight_currency, max_len=3, default="XCD", upper=True)
        transport_currency = self._clip(self.transport_currency, max_len=3, default="XCD", upper=True)
        total_vehicles = max(self.total_number_of_vehicles or 0, 0)
        customs_office_code = self._validate_reference_code(self.customs_office_code, _("Customs Office Code"))
        place_departure_code = self._validate_reference_code(self.place_of_departure_code, _("Place of Departure Code"))
        place_destination_code = self._validate_reference_code(self.place_of_destination_code, _("Place of Destination Code"))

        scheduled = getattr(self, "scheduled_date", None) or getattr(self, "date_done", None)
        done = getattr(self, "date_done", None) or scheduled

        root = etree.Element("Awmds", nsmap={"xsi": "http://www.w3.org/2001/XMLSchema-instance"})
        root.set("{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation", "Awmds.xsd")

        general_segment = etree.SubElement(root, "General_segment")
        general_segment_id = etree.SubElement(general_segment, "General_segment_id")
        self._xml_text(general_segment_id, "Customs_office_code", customs_office_code)
        self._xml_text(general_segment_id, "Voyage_number", voyage_number)
        self._xml_text(general_segment_id, "Date_of_departure", self._aw_date(scheduled))
        self._xml_text(general_segment_id, "Date_of_arrival", self._aw_date(done))
        self._xml_text(general_segment_id, "Time_of_arrival", self._aw_time(done))

        totals_segment = etree.SubElement(general_segment, "Totals_segment")
        self._xml_text(totals_segment, "Total_number_of_bols", self._aw_number(total_bols))
        self._xml_text(totals_segment, "Total_number_of_packages", self._aw_number(total_packages))
        self._xml_text(totals_segment, "Total_number_of_containers", "0")
        self._xml_text(totals_segment, "Total_number_of_vehicles", str(total_vehicles))
        self._xml_text(totals_segment, "Total_gross_mass", self._aw_number(total_gross_mass))

        transport_information = etree.SubElement(general_segment, "Transport_information")
        carrier = etree.SubElement(transport_information, "Carrier")
        self._xml_text(carrier, "Carrier_code", carrier_code)
        shipping_agent = etree.SubElement(transport_information, "Shipping_Agent")
        self._xml_text(shipping_agent, "Shipping_Agent_code", shipping_agent_code)
        self._xml_text(transport_information, "Mode_of_transport_code", mode_of_transport_code)
        self._xml_text(transport_information, "Identity_of_transporter", identity_of_transporter)
        self._xml_text(transport_information, "Nationality_of_transporter_code", nationality_of_transporter_code)
        self._xml_text(transport_information, "Place_of_transporter", place_of_transporter)
        self._xml_text(transport_information, "Registration_number_of_transport_code", registration_number_of_transport_code)
        self._xml_text(transport_information, "Date_of_registration", self._aw_date(self.create_date))
        self._xml_text(transport_information, "Master_information", master_information)

        load_unload_place = etree.SubElement(general_segment, "Load_unload_place")
        self._xml_text(load_unload_place, "Place_of_departure_code", place_departure_code)
        self._xml_text(load_unload_place, "Place_of_destination_code", place_destination_code)

        tonnage = etree.SubElement(general_segment, "Tonnage")
        self._xml_text(tonnage, "Tonnage_net_weight", self._aw_number(total_gross_mass))
        self._xml_text(tonnage, "Tonnage_gross_weight", self._aw_number(total_gross_mass))

        for line_number, pkg in enumerate(packages, start=1):
            bol_segment = etree.SubElement(root, "Bol_segment")

            bol_id = etree.SubElement(bol_segment, "Bol_id")
            self._xml_text(bol_id, "Bol_reference", self._clip(pkg.container_number, max_len=25, default="AWB%022d" % line_number))
            self._xml_text(bol_id, "Line_number", str(line_number))
            self._xml_text(bol_id, "Bol_nature", self.bol_nature or "23")
            self._xml_text(bol_id, "Bol_type_code", bol_type_code)
            self._xml_text(bol_id, "FAS_Liner_Cargo", self.fas_liner_cargo or "F")

            bol_transport = etree.SubElement(bol_segment, "Transport_information")
            bol_carrier = etree.SubElement(bol_transport, "Carrier")
            self._xml_text(bol_carrier, "Carrier_code", carrier_code)
            bol_shipping_agent = etree.SubElement(bol_transport, "Shipping_Agent")
            self._xml_text(bol_shipping_agent, "Shipping_Agent_code", shipping_agent_code)

            bol_load_unload = etree.SubElement(bol_segment, "Load_unload_place")
            self._xml_text(bol_load_unload, "Place_of_loading_code", place_departure_code)
            self._xml_text(bol_load_unload, "Place_of_unloading_code", place_destination_code)

            traders_segment = etree.SubElement(bol_segment, "Traders_segment")
            exporter = etree.SubElement(traders_segment, "Exporter")
            self._xml_text(exporter, "Exporter_name", self._clip(pkg.supplier_id.name if pkg.supplier_id else "", max_len=140, default=""))
            self._xml_text(exporter, "Exporter_address", self._value_or_default(self._partner_address(pkg.supplier_id), ""))

            notify = etree.SubElement(traders_segment, "Notify")
            self._xml_text(notify, "Notify_name", self._clip(pkg.customer_id.name if pkg.customer_id else "", max_len=140, default=""))
            self._xml_text(notify, "Notify_address", self._value_or_default(self._partner_address(pkg.customer_id), ""))

            consignee_el = etree.SubElement(traders_segment, "Consignee")
            self._xml_text(consignee_el, "Consignee_name", self._clip(pkg.customer_id.name if pkg.customer_id else "", max_len=140, default=""))
            self._xml_text(consignee_el, "Consignee_address", self._value_or_default(self._partner_address(pkg.customer_id), ""))

            pkg_count = max(pkg.package_count or 1, 1)
            gross_mass = max(pkg.weight or 0.0, 0.0)

            goods_segment = etree.SubElement(bol_segment, "Goods_segment")
            self._xml_text(goods_segment, "Number_of_packages", str(pkg_count))
            self._xml_text(goods_segment, "Package_type_code", package_type_code)
            self._xml_text(goods_segment, "Gross_mass", self._aw_number(gross_mass))
            self._xml_text(goods_segment, "Shipping_marks", self._clip(pkg.customer_id.name if pkg.customer_id else "", max_len=2000, default=""))
            self._xml_text(goods_segment, "Goods_description", self._clip(pkg.description, max_len=2000, default="GOODS"))

            seals_segment = etree.SubElement(goods_segment, "Seals_segment")
            self._xml_text(seals_segment, "Number_of_seals", str(seals_count))
            self._xml_text(seals_segment, "Marks_of_seals", marks_of_seals)
            self._xml_text(seals_segment, "Sealing_party_code", sealing_party_code)

            self._xml_text(goods_segment, "Volume_in_cubic_meters", self._aw_number(max(pkg.volume or 0.0, 0.0)))
            self._xml_text(goods_segment, "Num_of_ctn_for_this_bol", "0")
            self._xml_text(goods_segment, "Num_of_vehicles_for_this_bol", "0")

            value_segment = etree.SubElement(bol_segment, "Value_segment")
            freight_segment = etree.SubElement(value_segment, "Freight_segment")
            self._xml_text(freight_segment, "PC_indicator", freight_pc_indicator)
            self._xml_text(freight_segment, "Freight_value", self._aw_number(max(self.freight_value or 0.0, 0.0)))
            self._xml_text(freight_segment, "Freight_currency", freight_currency)

            transport_segment = etree.SubElement(value_segment, "Transport_segment")
            self._xml_text(transport_segment, "Transport_value", self._aw_number(max(self.transport_value or 0.0, 0.0)))
            self._xml_text(transport_segment, "Transport_currency", transport_currency)

            location = etree.SubElement(bol_segment, "Location")
            self._xml_text(location, "Location_code", "")

        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
