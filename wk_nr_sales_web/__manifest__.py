# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name"          : "NR Sales and Services Website",
    "summary"       : """CUSTOM : Website to interact with NR Sales services.""",
    "category"      : "Website/Website",
    "version"       : "1.0.0",
    "sequence"      : 1,
    "author"        : "Webkul Software Pvt. Ltd.",
    "license"       : "Other proprietary",
    "website"       : "https://store.webkul.com/",
    "description"   : """website to interact with NR Sales services.""",
    "depends"       : ["website", "portal", "mail", "product", "account", "stock", "stock_picking_batch", "whatsapp"],
    "data"          : [
                        "security/ir.model.access.csv",
                        "security/ir_rules.xml",
                        "data/mail_template_data.xml",
                        "data/delivery_request_data.xml",
                        "data/nr_whatsapp_templates.xml",
                        "views/delivery_request_views.xml",
                        "views/res_partner_views.xml",
                        "views/nr_tariff_config_views.xml",
                        "views/nr_sales_config_views.xml",
                        "views/grant_portal_wizard_views.xml",
                        "views/create_invoice_wizard_views.xml",
                        "views/nr_sales_billing_wizard_views.xml",
                        "views/account_move_line_views.xml",
                        "views/nr_document_check_wizard_views.xml",
                        "views/parcel_received_wizard_views.xml",
                        "views/submit_wizard_views.xml",
                        "views/nr_sales_registration_templates.xml",
                        "views/portal_delivery_request_templates.xml",
                    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "pre_init_hook": "pre_init_check",
}
