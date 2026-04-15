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
    "name": "ASYCUDA Integration",
    "summary": """CUSTOM : ASYCUDA Manifest XML (AWMDS) Integration""",
    "category": "Inventory/Inventory",
    "version": "1.0.0",
    "sequence": 1,
    "author": "Webkul Software Pvt. Ltd.",
    "license": "Other proprietary",
    "website": "https://store.webkul.com/",
    "description": """Generate ASYCUDA World Manifest XML (AWMDS) from stock pickings.""",
    "depends": ["stock"],
    "external_dependencies": {
        "python": ["lxml"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/stock_picking_views.xml",
        "views/manifest_import_wizard_views.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "pre_init_hook": "pre_init_check",
}
