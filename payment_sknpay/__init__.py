# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from . import controllers
from . import models

from odoo.fields import Command
from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(env):
    setup_provider(env, 'sknpay')
    providers = env['payment.provider'].with_context(active_test=False).search(
        [('code', '=', 'sknpay')]
    )
    methods = env['payment.method'].with_context(active_test=False).search(
        [('code', 'in', ['card', 'visa', 'mastercard'])]
    )
    providers.write({'payment_method_ids': [Command.set(methods.ids)]})


def uninstall_hook(env):
    reset_payment_provider(env, 'sknpay')

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if server_serie != '19.0':
        raise UserError('Module support Odoo series 19.0 found {}.'.format(server_serie))
    return True
