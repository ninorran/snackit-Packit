# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import api, fields, models, _

from odoo.fields import Domain
from odoo.tools import formatLang

class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_multi_currency = fields.Boolean(string="Multi Currency")
    apply_exchange_difference = fields.Boolean(
        string="Apply Exchnage Difference", default=True)
    multi_currency_ids = fields.Many2many(
        "res.currency", string="Seleced Currencies")


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    is_multi_currency_payment = fields.Boolean(string="Multi Currency Payment")
    other_currency_id = fields.Many2one(
        'res.currency', string='Other Currency')
    other_currency_rate = fields.Float(string='Conversion Rate', digits=(
        12, 6), help='Conversion rate from company currency to order currency.')
    other_currency_amount = fields.Float(string='Currency Amount')

class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        result = super(ReportSaleDetails, self).get_sale_details(
            date_start, date_stop, config_ids, session_ids)
        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]
        domain = Domain.AND([domain,
                    [('date_order', '>=', fields.Datetime.to_string(result.get('date_start'))),
                    ('date_order', '<=', fields.Datetime.to_string(result.get('date_stop')))]
                    ])
        orders = self.env['pos.order'].search(domain)
        if orders.payment_ids.ids:
            query = """
                SELECT {group_by_field}, sum(other_currency_amount) AS amount
                FROM pos_payment
                WHERE id IN %s
                GROUP BY {group_by_field}
                """
            self._cr.execute(query.format(
                group_by_field='other_currency_id'), (tuple(orders.payment_ids.ids),))
            res = self._cr.dictfetchall()
            amount = []
            currency_sign = []
            symbol = []
            order_with_curr = {}
            data = {}
            for rec in res:
                other_currency = self.env['res.currency'].browse(
                    rec.get('other_currency_id'))
                total_amount = rec.get('amount')
                if other_currency.name and other_currency.symbol and (total_amount is not None):
                    currency_sign.append(other_currency.name)
                    symbol.append(other_currency.symbol)
                    total_amount_currency = round(total_amount, 2)
                    amount.append(total_amount_currency)
            result["currency_amount"] = False
            if amount and currency_sign and symbol:
                order_with_curr["amount"] = amount
                order_with_curr["currency_sign"] = currency_sign
                order_with_curr["symbol"] = symbol
                for i, curr in enumerate(order_with_curr['currency_sign']):
                    data[curr] = str(order_with_curr["symbol"][i]) + \
                        str(order_with_curr["amount"][i])
                result["currency_amount"] = data
                for rec in result["currency_amount"]:
                    result["symbol"]=rec
                    result["amount"]=result["currency_amount"][rec]
        return result


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_enable_multi_currency = fields.Boolean(
        related='pos_config_id.enable_multi_currency', readonly=False)

    pos_apply_exchange_difference = fields.Boolean(
        related='pos_config_id.apply_exchange_difference', readonly=False)

    pos_multi_currency_ids = fields.Many2many(
        related='pos_config_id.multi_currency_ids', readonly=False)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _load_pos_data_domain(self, data,config):
        domain =super()._load_pos_data_domain(data, config)
        if config.enable_multi_currency and len(config.multi_currency_ids) >0:
            return []
        return domain
class PosSession(models.Model):
    _inherit = 'pos.session'

    def get_closing_control_data(self):
        result = super().get_closing_control_data()
        orders = self.env['pos.order'].browse(self.order_ids.ids)
        
        if orders.payment_ids.ids:
            query = """
                SELECT {group_by_field}, sum(other_currency_amount) AS amount
                FROM pos_payment
                WHERE id IN %s
                GROUP BY {group_by_field}
                """
            self._cr.execute(query.format(
                group_by_field='other_currency_id'), (tuple(orders.payment_ids.ids),))
            res= self._cr.dictfetchall()
            amount = []
            currency_sign = []
            symbol=[]
            order_with_curr={}
            data={}
            for rec in res:
                other_currency = self.env['res.currency'].browse(
                    rec.get('other_currency_id'))
                total_amount = rec.get('amount')
                if other_currency.name and other_currency.symbol and (total_amount is not None):
                    currency_sign.append(other_currency.name)
                    symbol.append(other_currency.symbol)
                    total_amount_currency = round(total_amount, 2)
                    amount.append(total_amount_currency)
            result["currency_amount"] = False
            if amount and currency_sign and symbol:
                order_with_curr["amount"] = amount
                order_with_curr["currency_sign"] = currency_sign
                order_with_curr["symbol"] = symbol
                for i, curr in enumerate(order_with_curr['currency_sign']):
                    data[curr] = str(order_with_curr["symbol"][i])+str(order_with_curr["amount"][i])
                result["currency_amount"] = data
        return result
    
class AccountMove(models.Model):
    _inherit = "account.move"
    
    @api.depends('move_type', 'line_ids.amount_residual')
    def _compute_payments_widget_reconciled_info(self):
        for move in self:
            payments_widget_vals = {'title': _('Less Payment'), 'outstanding': False, 'content': []}
            reconciled_vals = []
            is_multi_currency = False

            if move.state == 'posted' and move.is_invoice(include_receipts=True):
                reconciled_partials = move.sudo()._get_all_reconciled_invoice_partials()

                for reconciled_partial in reconciled_partials:
                    counterpart_line = reconciled_partial['aml']
                    pos_payment = counterpart_line.move_id.sudo().pos_payment_ids
                    
                    if pos_payment and pos_payment.is_multi_currency_payment:
                        is_multi_currency = True

                        other_currency_amount = pos_payment.other_currency_amount
                        reconciled_vals.append({
                            'name': counterpart_line.name,
                            'journal_name': counterpart_line.journal_id.name,
                            'company_name': counterpart_line.journal_id.company_id.name if counterpart_line.journal_id.company_id != move.company_id else False,
                            'amount': reconciled_partial['amount'],
                            'currency_id': move.company_id.currency_id.id if reconciled_partial['is_exchange'] else reconciled_partial['currency'].id,
                            'date': counterpart_line.date,
                            'partial_id': reconciled_partial['partial_id'],
                            'account_payment_id': counterpart_line.payment_id.id,
                            'payment_method_name': counterpart_line.payment_id.payment_method_line_id.name,
                            'move_id': counterpart_line.move_id.id,
                            'ref': f"{counterpart_line.move_id.name} ({counterpart_line.move_id.ref})" if counterpart_line.move_id.ref else counterpart_line.move_id.name,
                            'is_exchange': reconciled_partial['is_exchange'],
                            'amount_company_currency': formatLang(self.env, abs(counterpart_line.balance), currency_obj=counterpart_line.company_id.currency_id),
                            'amount_foreign_currency': formatLang(self.env, abs(counterpart_line.amount_currency), currency_obj=counterpart_line.currency_id) if counterpart_line.currency_id else False,
                            'is_multi_currency': True,
                            'other_currency_id': pos_payment.other_currency_id,
                            'other_currency_amount': other_currency_amount,
                        })
                
                payments_widget_vals['content'] = reconciled_vals
            if is_multi_currency:
                move.invoice_payments_widget = payments_widget_vals if payments_widget_vals['content'] else False
            else:
                super()._compute_payments_widget_reconciled_info()