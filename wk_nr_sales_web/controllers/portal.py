# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

import base64

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class NrSalesPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'delivery_request_count' in counters:
            partner = request.env.user.partner_id
            DeliveryRequest = request.env['nr.delivery.request']
            values['delivery_request_count'] = (
                DeliveryRequest.search_count(self._delivery_request_domain(partner))
                if DeliveryRequest.has_access('read')
                else 0
            )
        return values

    def _delivery_request_domain(self, partner):
        return [('partner_id', 'child_of', [partner.commercial_partner_id.id])]

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------
    @http.route(
        ['/my/delivery-requests', '/my/delivery-requests/page/<int:page>'],
        type='http', auth='user', website=True,
    )
    def portal_my_delivery_requests(self, page=1, **kwargs):
        partner = request.env.user.partner_id
        DeliveryRequest = request.env['nr.delivery.request']
        domain = self._delivery_request_domain(partner)

        total = DeliveryRequest.search_count(domain)
        pager_values = portal_pager(
            url='/my/delivery-requests',
            total=total,
            page=page,
            step=10,
        )
        records = DeliveryRequest.search(
            domain,
            order='create_date desc',
            limit=10,
            offset=pager_values['offset'],
        )

        return request.render('wk_nr_sales_web.portal_delivery_request_list', {
            'delivery_requests': records.sudo(),
            'pager': pager_values,
            'page_name': 'delivery_requests',
        })

    # ------------------------------------------------------------------
    # Detail
    # ------------------------------------------------------------------
    @http.route(
        '/my/delivery-requests/<int:request_id>',
        type='http', auth='public', website=True,
    )
    def portal_delivery_request_detail(self, request_id, access_token=None, **kwargs):
        try:
            record_sudo = self._document_check_access(
                'nr.delivery.request', request_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my/delivery-requests')

        values = {
            'delivery_request': record_sudo,
            'page_name': 'delivery_request_detail',
        }
        values.update(self._get_page_view_values(
            record_sudo, access_token, values,
            'my_delivery_requests_history', False, **kwargs,
        ))
        return request.render('wk_nr_sales_web.portal_delivery_request_detail', values)

    # ------------------------------------------------------------------
    # Create form
    # ------------------------------------------------------------------
    @http.route('/my/delivery-requests/new', type='http', auth='user', website=True)
    def portal_delivery_request_new(self, **kwargs):
        return request.render('wk_nr_sales_web.portal_delivery_request_form', {
            'page_name': 'delivery_request_new',
            'errors': {},
            'values': {},
        })

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------
    @http.route(
        '/my/delivery-requests/submit',
        type='http', auth='user', website=True, methods=['POST'], csrf=True,
    )
    def portal_delivery_request_submit(self, **post):
        errors = {}

        # Collect line data: item_name[], item_description[], item_quantity[]
        item_names = request.httprequest.form.getlist('item_name')
        item_descriptions = request.httprequest.form.getlist('item_description')
        item_quantities = request.httprequest.form.getlist('item_quantity')
        item_notes = request.httprequest.form.getlist('item_notes')

        lines = []
        for name, desc, qty, note in zip(
            item_names, item_descriptions, item_quantities,
            item_notes or [''] * len(item_names),
        ):
            name = name.strip()
            if not name:
                continue
            try:
                quantity = float(qty) if qty.strip() else 1.0
            except ValueError:
                quantity = 1.0
            lines.append({
                'name': name,
                'description': desc.strip() or False,
                'quantity': quantity,
                'notes': note.strip() or False,
            })

        if not lines:
            errors['lines'] = 'Please add at least one item.'

        if errors:
            return request.render('wk_nr_sales_web.portal_delivery_request_form', {
                'page_name': 'delivery_request_new',
                'errors': errors,
                'values': post,
            })

        partner = request.env.user.partner_id
        record = request.env['nr.delivery.request'].sudo().create({
            'partner_id': partner.id,
            'line_ids': [(0, 0, line) for line in lines],
        })

        # Handle file uploads for each document type
        doc_fields = {
            'supplier_invoice': 'supplier_invoice_ids',
            'purchase_invoice': 'purchase_invoice_ids',
            'shipping_document': 'shipping_document_ids',
        }
        for file_key, field_name in doc_fields.items():
            uploaded_files = request.httprequest.files.getlist(file_key)
            attachment_ids = []
            for f in uploaded_files:
                if not f.filename:
                    continue
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': f.filename,
                    'datas': base64.b64encode(f.read()),
                    'res_model': 'nr.delivery.request',
                    'res_id': record.id,
                    'mimetype': f.content_type,
                })
                attachment_ids.append(attachment.id)
            if attachment_ids:
                record[field_name] = [(4, aid) for aid in attachment_ids]

        return request.redirect(f'/my/delivery-requests/{record.id}')

    # ------------------------------------------------------------------
    # Update (draft only)
    # ------------------------------------------------------------------
    @http.route(
        '/my/delivery-requests/<int:request_id>/update',
        type='http', auth='user', website=True, methods=['POST'], csrf=True,
    )
    def portal_delivery_request_update(self, request_id, **post):
        try:
            record_sudo = self._document_check_access(
                'nr.delivery.request', request_id, access_token=None
            )
        except (AccessError, MissingError):
            return request.redirect('/my/delivery-requests')

        # Block all edits once a picking has been created
        if record_sudo.active_picking_count > 0:
            return request.redirect(f'/my/delivery-requests/{request_id}')

        # --- rebuild line_ids (draft only) ---
        if record_sudo.state == 'draft':
            item_names = request.httprequest.form.getlist('item_name')
            item_descriptions = request.httprequest.form.getlist('item_description')
            item_quantities = request.httprequest.form.getlist('item_quantity')
            item_notes = request.httprequest.form.getlist('item_notes')

            lines = []
            for name, desc, qty, note in zip(
                item_names, item_descriptions, item_quantities,
                item_notes or [''] * len(item_names),
            ):
                name = name.strip()
                if not name:
                    continue
                try:
                    quantity = float(qty) if qty.strip() else 1.0
                except ValueError:
                    quantity = 1.0
                lines.append((0, 0, {
                    'name': name,
                    'description': desc.strip() or False,
                    'quantity': quantity,
                    'notes': note.strip() or False,
                }))

            record_sudo.sudo().write({
                'line_ids': [(5, 0, 0)] + lines,
            })

        # --- delete checked documents ---
        delete_fields = {
            'delete_doc_supplier_invoice': 'supplier_invoice_ids',
            'delete_doc_purchase_invoice': 'purchase_invoice_ids',
            'delete_doc_shipping_document': 'shipping_document_ids',
        }
        for form_key, field_name in delete_fields.items():
            ids_to_delete = request.httprequest.form.getlist(form_key)
            if ids_to_delete:
                doc_ids = [int(i) for i in ids_to_delete if i.isdigit()]
                record_sudo.sudo().write({field_name: [(3, did) for did in doc_ids]})

        # --- upload new documents ---
        doc_fields = {
            'supplier_invoice': 'supplier_invoice_ids',
            'purchase_invoice': 'purchase_invoice_ids',
            'shipping_document': 'shipping_document_ids',
        }
        for file_key, field_name in doc_fields.items():
            uploaded_files = request.httprequest.files.getlist(file_key)
            attachment_ids = []
            for f in uploaded_files:
                if not f.filename:
                    continue
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': f.filename,
                    'datas': base64.b64encode(f.read()),
                    'res_model': 'nr.delivery.request',
                    'res_id': record_sudo.id,
                    'mimetype': f.content_type,
                })
                attachment_ids.append(attachment.id)
            if attachment_ids:
                record_sudo.sudo().write({field_name: [(4, aid) for aid in attachment_ids]})

        return request.redirect(f'/my/delivery-requests/{request_id}')
