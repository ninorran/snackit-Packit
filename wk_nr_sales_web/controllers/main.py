# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import http
from odoo.http import request


class NrSalesRegistration(http.Controller):

    def _get_address_render_values(self):
        countries = request.env['res.country'].sudo().search([], order='name asc')
        return {
            'countries': countries,
            'states': [],
        }

    @http.route('/nr-sales/register', type='http', auth='public', website=True, methods=['GET'])
    def registration_form(self, **kwargs):
        render_values = self._get_address_render_values()
        partner = request.env.user.partner_id
        if not request.env.user._is_public() and partner.nr_sales_customer:
            render_values['already_registered'] = True
            render_values['partner_name'] = partner.name
            render_values['nr_sales_state'] = partner.nr_sales_state
        return request.render('wk_nr_sales_web.nr_sales_registration_form', render_values)

    @http.route('/nr-sales/register/states', type='jsonrpc', auth='public', website=True, methods=['POST'])
    def get_states(self, country_id=None):
        if not country_id:
            return []
        states = request.env['res.country.state'].sudo().search(
            [('country_id', '=', int(country_id))], order='name asc'
        )
        return [{'id': s.id, 'name': s.name} for s in states]

    @http.route('/nr-sales/register/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def registration_submit(self, **post):
        name = post.get('name', '').strip()
        phone = post.get('phone', '').strip()
        street = post.get('street', '').strip()
        street2 = post.get('street2', '').strip()
        city = post.get('city', '').strip()
        zip_code = post.get('zip', '').strip()
        country_id = post.get('country_id', '').strip()
        state_id = post.get('state_id', '').strip()
        email = post.get('email', '').strip()

        errors = {}

        if not name:
            errors['name'] = 'Name is required.'
        if not phone:
            errors['phone'] = 'Phone number is required.'
        if not street:
            errors['street'] = 'Street address is required.'
        if not city:
            errors['city'] = 'City is required.'
        if not country_id:
            errors['country_id'] = 'Country is required.'

        if email:
            existing = request.env['res.partner'].sudo().search(
                [('email', '=ilike', email)], limit=1
            )
            if existing:
                errors['email'] = 'This email address is already registered.'

        if errors:
            render_values = self._get_address_render_values()
            # Re-populate states for the selected country so the dropdown is not empty
            if country_id:
                render_values['states'] = request.env['res.country.state'].sudo().search(
                    [('country_id', '=', int(country_id))], order='name asc'
                )
            render_values.update({'errors': errors, 'values': post})
            return request.render('wk_nr_sales_web.nr_sales_registration_form', render_values)

        partner_vals = {
            'name': name,
            'phone': phone,
            'street': street,
            'street2': street2 or False,
            'city': city,
            'zip': zip_code or False,
            'country_id': int(country_id),
            'state_id': int(state_id) if state_id else False,
            'email': email or False,
            'nr_sales_customer': True,
            'nr_sales_state': 'registration_request',
        }
        partner = request.env['res.partner'].sudo().create(partner_vals)
        template = request.env['nr.whatsapp.event.config'].sudo()._get_template_for_event('registration')
        if template and (partner.mobile or partner.phone):
            try:
                request.env['whatsapp.composer'].sudo().create({
                    'res_model': 'res.partner',
                    'res_ids': partner.ids,
                    'wa_template_id': template.id,
                })._send_whatsapp_template(force_send_by_cron=True)
            except Exception:
                pass

        return request.render('wk_nr_sales_web.nr_sales_registration_success', {
            'partner_name': name,
        })
