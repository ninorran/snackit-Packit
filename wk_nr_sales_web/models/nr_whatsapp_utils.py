# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################


def send_nr_partner_whatsapp(env, event_key, partner):
    """Send a WhatsApp notification to a res.partner for the given event key.
    Silently skips if no approved template is configured or partner has no mobile."""
    template = env['nr.whatsapp.event.config']._get_template_for_event(event_key)
    if not template or not (partner.mobile or partner.phone):
        return
    try:
        env['whatsapp.composer'].sudo().create({
            'res_model': 'res.partner',
            'res_ids': partner.ids,
            'wa_template_id': template.id,
        })._send_whatsapp_template(force_send_by_cron=True)
    except Exception:
        pass
