/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { formatFloat, roundDecimals as round_di } from "@web/core/utils/numbers";
import { Component, onMounted } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

patch(PaymentScreen.prototype, {
  setup() {
    this.pos = usePos();
    this.dialog = useService("dialog");
    super.setup();
  },

  updateSelectedPaymentline(amount = false) {
    if (this.selectedPaymentLine?.is_multi_currency_payment) {
      if (this.paymentLines.every((line) => line.paid)) {
        this.currentOrder.addPaymentline(this.payment_methods_from_config[0]);
      }
      if (!this.selectedPaymentLine) {
        return;
      } // do nothing if no selected payment line
      if (amount === false) {
        if (this.numberBuffer.get() === null) {
          amount = null;
        } else if (this.numberBuffer.get() === "") {
          amount = 0;
        } else {
          amount = this.numberBuffer.getFloat();
        }
      }
      // disable changing amount on paymentlines with running or done payments on a payment terminal
      const payment_terminal = this.selectedPaymentLine.payment_method_id.payment_terminal;
      const hasCashPaymentMethod = this.payment_methods_from_config.some(
        (method) => method.type === "cash"
      );
      if (
        !hasCashPaymentMethod &&
        amount > this.currentOrder.getDue() + this.selectedPaymentLine.amount
      ) {
        this.selectedPaymentLine.setAmount(0);
        this.numberBuffer.set(this.currentOrder.getDue().toString());
        amount = this.currentOrder.getDue();
        this.showMaxValueError();
      }
      if (
        payment_terminal &&
        !["pending", "retry"].includes(this.selectedPaymentLine.getPaymentStatus())
      ) {
        return;
      }
      if (amount === null) {
        this.deletePaymentLine(this.selectedPaymentLine.uuid);
      } else {
        var amt = ((this.numberBuffer.getFloat() * this.pos.currency.rate) / this.selectedPaymentLine.other_currency_rate);
        this.selectedPaymentLine.otc_amount = amt;
        this.selectedPaymentLine.setAmount(amt);
        this.selectedPaymentLine.other_currency_amount = this.pos.get_other_currency_amount(this.selectedPaymentLine);
      }
    }
    else {
      super.updateSelectedPaymentline();
    }
  },

  clickmulticurrency() {
    var self = this;
    var order = self.pos.getOrder();
    if (order && order.use_multi_currency) {
      order.use_multi_currency = false
      if (order && order.payment_ids && order.payment_ids.length) {
        order.payment_ids.forEach(function (paymentline) {
          paymentline.other_currency_id = false
          paymentline.other_currency_rate = 0
          paymentline.other_currency_amount = 0
          paymentline.is_multi_currency_payment = false
          if (self.pos.config.currency_id && self.pos.config.currency_id.id) {
            paymentline.currency_id = self.pos.config.currency_id.id

          }
        })
      }
    } else {
      order.use_multi_currency = true
    }
  },

  async addNewPaymentLine(paymentMethod) {
    if (this.pos.config.enable_multi_currency && this.currentOrder.use_multi_currency) {
      var currency_id = this.pos.config.currency_id.id;
      await this.dialog.add(MultiCurrencyPopup, {
        payment_id: paymentMethod,
        getPayload: (currency) => {
          currency_id = parseInt(currency)
          this.currentOrder.addPaymentline(paymentMethod);
          var paymentLine = this.currentOrder.getSelectedPaymentline()
          if (paymentLine) {
            paymentLine.currency_id = currency_id
            if (this.pos.currency_by_id && this.pos.config.enable_multi_currency && this.currentOrder.use_multi_currency) {
              var currency_data = this.pos.data.models["res.currency"].get(currency_id)
              paymentLine.other_currency_id = currency_data
              if (currency_data) {
                paymentLine.other_currency_rate = currency_data.rate
              }
              paymentLine.is_multi_currency_payment = true
              paymentLine.otc_amount = paymentLine.getAmount()
              paymentLine.other_currency_amount = this.pos.get_other_currency_amount(paymentLine)
            }
          }
          this.numberBuffer.reset();
          this.payment_interface = paymentMethod.payment_terminal;
          if (this.payment_interface) {
            paymentLine.set_payment_status('pending');
          }
        },
      })
    }
    else {
      return await super.addNewPaymentLine(paymentMethod);
    }

  },
});

export class MultiCurrencyPopup extends Component {
  static template = "pos_payment_in_multi_currency.MultiCurrencyPopup";
  static components = { Dialog };
  static props = {
    getPayload: Function,
    close: Function,
    payment_id: { type: Object, optional: true },
  };
  amountCheck() {
    const currencyId = document.querySelector('.wk-selected-currency')?.value;

    if (currencyId) {
      const currency = this.pos.currency_by_id[currencyId];
      if (currency) {
        document.querySelector('.wk-exchange-rate').innerHTML = currency.rate;

        let rate = (currency.rate * 1) / this.pos.currency_by_id[this.pos.config.currency_id.id].rate;
        rate = formatFloat(round_di(rate, 5), { digits: [69, 5] });

        document.querySelector('.wk-currency-amount').innerHTML = rate;
        document.querySelector('.wk-currency-name').innerHTML = `${currency.name} (${currency.symbol})`;
      }
    }
  }
  setup() {
    this.pos = usePos();
    super.setup();
    onMounted(this.onMounted);
  }
  onMounted() {
    var self = this;
    self.amountCheck();
  }
  selected_currency() {
    var self = this;
    self.amountCheck();
  }
  confirm() {
    const currencyId = document.querySelector('.wk-selected-currency')?.value;
    this.props.getPayload(currencyId);
    this.props.close();
  }
};

