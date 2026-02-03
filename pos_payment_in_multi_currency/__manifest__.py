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
    "name"              :  "POS Multi Currency",
    "summary"           :  """CUSTOM : Pos Multi Currency provide a multi-currency facility to your customers in POS.Multi Currency|Payment In Multi Currency|Currency|Multiple currency""",
    "category"          :  "Point Of Sale",
    "version"           :  "1.0.2",
    "author"            :  "Webkul Software Pvt. Ltd.",
    "license"           :  "Other proprietary",
    "website"           :  "https://store.webkul.com/Odoo-POS-Multi-Currency.html",
    "description"       :  """Pos Multi Currency
    Multiple Currencies
    Foreign Currency
    Exchange Money
    Payment Multi-Currency
    """,
    "live_test_url"     :  "http://odoodemo.webkul.com/?module=pos_payment_in_multi_currency&custom_url=/pos/auto",
    "depends"           :  ['point_of_sale'],
    "data"              :  ['views/pos_config.xml',
                            'views/report_session.xml',
                            'views/report_invoice.xml'
                            ],
    "assets"            :   {
                            'point_of_sale._assets_pos': [
                                'pos_payment_in_multi_currency/static/src/**/*',
                            ],
                                },
    "demo"              :  ['demo/demo.xml', ],
    "images"            :  ['static/description/Banner.png'],
    "application"       :  True,
    "installable"       :  True,
    "auto_install"      :  False,
    "price"             :  149,
    "currency"          :  "USD",
    "pre_init_hook"     :  "pre_init_check",
}
