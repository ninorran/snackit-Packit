# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from . import models, controllers


def pre_init_check(cr):
    from odoo.exceptions import UserError
    from odoo.service import common

    version_info = common.exp_version()
    server_serie = version_info.get("server_serie")
    if server_serie != "19.0":
        raise UserError(f"Module supports Odoo series 19.0 only, found {server_serie}.")
    return True
