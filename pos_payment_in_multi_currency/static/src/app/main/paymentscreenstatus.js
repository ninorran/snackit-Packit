/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";  

patch(PaymentScreenStatus.prototype, {
    setup() {
      this.pos = usePos();
      super.setup();
    },
    
    get changeTextmc() {
      if (this.pos.config.enable_multi_currency && this.props.order.use_multi_currency) {
        var amt = this.pos.format_currency_n_symbol(this.pos.get_change_mc(this.props.order.change, this.props.order.getSelectedPaymentline()), 0.0001);
        var currency_id = this.props.order.getSelectedPaymentline().other_currency_id;
        return this.pos.formating(amt, currency_id)
      }
      else {
        return this.env.utils.formatCurrency(this.props.order.change);
      }
    },
    get totalDueTextmc() {
      if (this.pos.config.enable_multi_currency && this.props.order.use_multi_currency) {
        var currency_id = this.props.order.getSelectedPaymentline().other_currency_id;
        var due = this.pos.get_change_mc(this.props.order.priceIncl + this.props.order.appliedRounding, this.props.order.getSelectedPaymentline())
        var amt = this.pos.format_currency_n_symbol(
          due > 0 ? due : 0, 0.0001);
        return this.pos.formating(amt, currency_id)
      }
      else {
        return this.env.utils.formatCurrency(
          this.props.order.priceIncl + this.props.order.appliedRounding
        );
      }
    },
    get remainingTextmc() {
      if (this.pos.config.enable_multi_currency && this.props.order.use_multi_currency) {
        var currency_id = this.props.order.getSelectedPaymentline().other_currency_id;
        var rem = this.pos.get_change_mc(this.props.order.remainingDue, this.props.order.getSelectedPaymentline())
        var amt = this.pos.format_currency_n_symbol(
          rem > 0 ? rem : 0, 0.0001)
        return this.pos.formating(amt, currency_id)
      }
      else {
        return this.env.utils.formatCurrency(
          this.props.order.remainingDue > 0 ? this.props.order.remainingDue : 0
        );
      }
    },
    get convamount() {
      return this.env.utils.formatCurrency(this.props.order.getSelectedPaymentline().getAmount());
    }
});
