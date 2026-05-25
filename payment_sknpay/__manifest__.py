# -*- coding: utf-8 -*-
{
    'name': 'Payment Provider: SKNPay',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A payment provider for the Eastern Caribbean market (USD/XCD).",
    'description': " ",
    'author': 'Webkul Software Pvt. Ltd.',
    'depends': ['payment'],
    'data': [
        'views/payment_sknpay_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
