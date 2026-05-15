# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    _sql_constraints = [
        ('nr_sales_uid_unique', 'UNIQUE(nr_sales_uid)',
         'The NR Sales ID must be unique.'),
    ]

    nr_sales_customer = fields.Boolean(string='NR Sales Customer')
    nr_sales_uid = fields.Char(string='NR Sales ID', readonly=True, copy=False, index=True)
    nr_sales_state = fields.Selection([
        ('registration_request', 'Registration Request'),
        ('request_accepted', 'Request Accepted'),
        ('portal_access_sent', 'Portal Access Sent'),
        ('active', 'Active'),
        ('revoked', 'Revoked'),
    ], string='Customer Status', default='registration_request', tracking=True)

    delivery_request_count = fields.Integer(
        string='Delivery Requests',
        compute='_compute_delivery_request_count',
    )
    portal_user_count = fields.Integer(
        string='Portal Users',
        compute='_compute_portal_user_count',
    )

    def _compute_portal_user_count(self):
        for partner in self:
            partner.portal_user_count = len(partner.user_ids)

    @api.depends('nr_sales_customer')
    def _compute_delivery_request_count(self):
        counts = self.env['nr.delivery.request']._read_group(
            [('partner_id', 'in', self.ids)],
            groupby=['partner_id'],
            aggregates=['__count'],
        )
        count_map = {partner.id: count for partner, count in counts}
        for partner in self:
            partner.delivery_request_count = count_map.get(partner.id, 0)

    def action_open_portal_users(self):
        self.ensure_one()
        users = self.user_ids
        action = {
            'name': 'Portal Users',
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
        }
        if len(users) == 1:
            action.update({'view_mode': 'form', 'res_id': users.id})
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', users.ids)],
            })
        return action

    def action_grant_nr_portal_access(self):
        self.ensure_one()
        if not self.nr_sales_customer:
            return
        config = self.env['nr.sales.config']._get_config(self.env)
        wizard = self.env['nr.grant.portal.wizard'].create({'partner_id': self.id})
        return {
            'name': 'Grant Portal Access',
            'type': 'ir.actions.act_window',
            'res_model': 'nr.grant.portal.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_delivery_address_id': config.delivery_address_ids[:1].id or False,
            },
        }

    def action_revoke_nr_portal_access(self):
        self.ensure_one()
        if not self.nr_sales_customer:
            return
        wizard = self.env['portal.wizard'].create({'partner_ids': [(4, self.id)]})
        wizard_user = wizard.user_ids.filtered(lambda u: u.partner_id == self)
        if not wizard_user or not wizard_user.is_portal:
            self.sudo().write({'nr_sales_state': 'revoked'})
            return
        wizard_user.action_revoke_access()
        self.sudo().write({'nr_sales_state': 'revoked'})
